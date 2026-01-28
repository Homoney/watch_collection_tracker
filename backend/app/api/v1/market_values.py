from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, case

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.models.watch import Watch
from app.models.market_value import MarketValue
from app.models.collection import Collection
from app.models.reference import Brand
from app.schemas.market_value import (
    MarketValueCreate,
    MarketValueUpdate,
    MarketValueResponse,
    WatchAnalytics,
    CollectionAnalytics,
)

router = APIRouter()
collection_analytics_router = APIRouter()


@collection_analytics_router.get("/collection-analytics", response_model=CollectionAnalytics)
def get_collection_analytics(
    currency: str = Query("USD", description="Base currency for analytics"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get analytics for the entire collection: total value, ROI, breakdowns by brand/collection.
    Optimized with SQL aggregation queries for performance.
    Note: This simplified version assumes all values are in the same currency.
    """
    # Total watches count
    total_watches = db.query(func.count(Watch.id)).filter(
        Watch.user_id == current_user.id
    ).scalar() or 0

    # Total current value and purchase price (single query with aggregation)
    totals = db.query(
        func.sum(case(
            (Watch.current_market_currency == currency, Watch.current_market_value),
            else_=0
        )).label('total_current_value'),
        func.sum(case(
            (Watch.purchase_currency == currency, Watch.purchase_price),
            else_=0
        )).label('total_purchase_price')
    ).filter(
        Watch.user_id == current_user.id
    ).first()

    total_current_value = totals.total_current_value or Decimal('0')
    total_purchase_price = totals.total_purchase_price or Decimal('0')
    total_return = total_current_value - total_purchase_price

    # Calculate average ROI using SQL
    average_roi_result = db.query(
        func.avg(
            case(
                ((Watch.purchase_price > 0) &
                 (Watch.current_market_value.isnot(None)) &
                 (Watch.current_market_currency == currency) &
                 (Watch.purchase_currency == currency),
                 ((Watch.current_market_value - Watch.purchase_price) / Watch.purchase_price * 100)),
                else_=None
            )
        ).label('avg_roi')
    ).filter(
        Watch.user_id == current_user.id
    ).scalar()

    average_roi = float(average_roi_result) if average_roi_result else 0.0

    # Get top and worst performers (single query, sorted by ROI)
    performers = db.query(
        Watch.id,
        Watch.model,
        Brand.name.label('brand_name'),
        Watch.current_market_value,
        Watch.purchase_price,
        ((Watch.current_market_value - Watch.purchase_price) / Watch.purchase_price * 100).label('roi')
    ).outerjoin(Brand).filter(
        Watch.user_id == current_user.id,
        Watch.purchase_price > 0,
        Watch.current_market_value.isnot(None),
        Watch.current_market_currency == currency,
        Watch.purchase_currency == currency
    ).order_by(desc('roi')).all()

    # Format performers
    watch_rois = [
        {
            'watch_id': str(p.id),
            'model': p.model,
            'brand': p.brand_name or 'Unknown',
            'roi': float(p.roi),
            'current_value': float(p.current_market_value),
            'purchase_price': float(p.purchase_price),
        }
        for p in performers
    ]

    top_performers = watch_rois[:5]
    worst_performers = list(reversed(watch_rois[-5:])) if len(watch_rois) > 5 else []

    # Value by brand (single query with GROUP BY)
    brand_values = db.query(
        Brand.name,
        func.sum(Watch.current_market_value).label('total_value')
    ).join(Watch).filter(
        Watch.user_id == current_user.id,
        Watch.current_market_value.isnot(None),
        Watch.current_market_currency == currency
    ).group_by(Brand.name).all()

    value_by_brand = {bv.name: float(bv.total_value) for bv in brand_values}

    # Value by collection (single query with GROUP BY)
    collection_values = db.query(
        Collection.name,
        func.sum(Watch.current_market_value).label('total_value')
    ).join(Watch).filter(
        Watch.user_id == current_user.id,
        Watch.current_market_value.isnot(None),
        Watch.current_market_currency == currency
    ).group_by(Collection.name).all()

    value_by_collection = {cv.name: float(cv.total_value) for cv in collection_values}

    # Count total valuations
    total_valuations = db.query(func.count(MarketValue.id)).join(Watch).filter(
        Watch.user_id == current_user.id
    ).scalar() or 0

    return CollectionAnalytics(
        total_watches=total_watches,
        total_current_value=total_current_value,
        total_purchase_price=total_purchase_price,
        currency=currency,
        total_return=total_return,
        average_roi=average_roi,
        top_performers=top_performers,
        worst_performers=worst_performers,
        value_by_brand=value_by_brand,
        value_by_collection=value_by_collection,
        total_valuations=total_valuations,
    )


def verify_watch_ownership(watch_id: UUID, current_user: User, db: Session) -> Watch:
    """Verify that the current user owns the specified watch."""
    watch = db.query(Watch).filter(
        Watch.id == watch_id,
        Watch.user_id == current_user.id
    ).first()

    if not watch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watch not found"
        )

    return watch


@router.post("/{watch_id}/market-values", response_model=MarketValueResponse, status_code=status.HTTP_201_CREATED)
def create_market_value(
    watch_id: UUID,
    value_data: MarketValueCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new market value record for a watch.
    """
    # Verify watch ownership
    watch = verify_watch_ownership(watch_id, current_user, db)

    # Create market value record
    market_value = MarketValue(
        watch_id=watch.id,
        value=value_data.value,
        currency=value_data.currency,
        source=value_data.source,
        notes=value_data.notes,
        recorded_at=value_data.recorded_at if value_data.recorded_at else datetime.utcnow(),
    )

    db.add(market_value)

    # Update watch's current market value only if this is the most recent value
    if not watch.last_value_update or market_value.recorded_at >= watch.last_value_update:
        watch.current_market_value = value_data.value
        watch.current_market_currency = value_data.currency
        watch.last_value_update = market_value.recorded_at

    db.commit()
    db.refresh(market_value)

    return market_value


@router.get("/{watch_id}/market-values", response_model=List[MarketValueResponse])
def list_market_values(
    watch_id: UUID,
    start_date: Optional[datetime] = Query(None, description="Filter values from this date"),
    end_date: Optional[datetime] = Query(None, description="Filter values until this date"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all market value records for a watch, ordered by date (most recent first).
    Optionally filter by date range.
    """
    # Verify watch ownership
    watch = verify_watch_ownership(watch_id, current_user, db)

    # Build query
    query = db.query(MarketValue).filter(MarketValue.watch_id == watch.id)

    if start_date:
        query = query.filter(MarketValue.recorded_at >= start_date)
    if end_date:
        query = query.filter(MarketValue.recorded_at <= end_date)

    # Order by date descending and limit
    values = query.order_by(desc(MarketValue.recorded_at)).limit(limit).all()

    return values


@router.get("/{watch_id}/market-values/{value_id}", response_model=MarketValueResponse)
def get_market_value(
    watch_id: UUID,
    value_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific market value record.
    """
    # Verify watch ownership
    watch = verify_watch_ownership(watch_id, current_user, db)

    # Get market value
    market_value = db.query(MarketValue).filter(
        MarketValue.id == value_id,
        MarketValue.watch_id == watch.id
    ).first()

    if not market_value:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market value record not found"
        )

    return market_value


@router.put("/{watch_id}/market-values/{value_id}", response_model=MarketValueResponse)
def update_market_value(
    watch_id: UUID,
    value_id: UUID,
    value_data: MarketValueUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a market value record.
    """
    # Verify watch ownership
    watch = verify_watch_ownership(watch_id, current_user, db)

    # Get market value
    market_value = db.query(MarketValue).filter(
        MarketValue.id == value_id,
        MarketValue.watch_id == watch.id
    ).first()

    if not market_value:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market value record not found"
        )

    # Update fields if provided
    update_data = value_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(market_value, field, value)

    db.commit()
    db.refresh(market_value)

    # Recalculate watch's current value (always find the latest after update)
    latest_value = db.query(MarketValue).filter(
        MarketValue.watch_id == watch.id
    ).order_by(desc(MarketValue.recorded_at)).first()

    if latest_value:
        watch.current_market_value = latest_value.value
        watch.current_market_currency = latest_value.currency
        watch.last_value_update = latest_value.recorded_at
        db.commit()

    return market_value


@router.delete("/{watch_id}/market-values/{value_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_market_value(
    watch_id: UUID,
    value_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a market value record.
    """
    # Verify watch ownership
    watch = verify_watch_ownership(watch_id, current_user, db)

    # Get market value
    market_value = db.query(MarketValue).filter(
        MarketValue.id == value_id,
        MarketValue.watch_id == watch.id
    ).first()

    if not market_value:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market value record not found"
        )

    db.delete(market_value)
    db.commit()

    # Update watch's current value to the latest remaining value
    latest_value = db.query(MarketValue).filter(
        MarketValue.watch_id == watch.id
    ).order_by(desc(MarketValue.recorded_at)).first()

    if latest_value:
        watch.current_market_value = latest_value.value
        watch.current_market_currency = latest_value.currency
        watch.last_value_update = latest_value.recorded_at
    else:
        watch.current_market_value = None
        watch.last_value_update = None

    db.commit()

    return None


@router.get("/{watch_id}/analytics", response_model=WatchAnalytics)
def get_watch_analytics(
    watch_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get analytics for a specific watch: ROI, value changes, etc.
    """
    # Verify watch ownership
    watch = verify_watch_ownership(watch_id, current_user, db)

    # Get all market values for this watch
    values = db.query(MarketValue).filter(
        MarketValue.watch_id == watch.id
    ).order_by(MarketValue.recorded_at).all()

    # Calculate analytics
    total_valuations = len(values)
    first_valuation_date = values[0].recorded_at if values else None
    latest_valuation_date = values[-1].recorded_at if values else None

    current_value = watch.current_market_value
    current_currency = watch.current_market_currency
    purchase_price = watch.purchase_price
    purchase_currency = watch.purchase_currency

    # Calculate returns (simplified - assuming same currency for now)
    total_return = None
    roi_percentage = None
    annualized_return = None

    if current_value and purchase_price and current_currency == purchase_currency:
        total_return = current_value - purchase_price
        roi_percentage = float((total_return / purchase_price) * 100)

        # Calculate annualized return if we have purchase date
        if watch.purchase_date:
            days_held = (datetime.utcnow() - watch.purchase_date).days
            if days_held > 0:
                years_held = days_held / 365.25
                annualized_return = ((float(current_value) / float(purchase_price)) ** (1 / years_held) - 1) * 100

    # Calculate value changes over time periods
    now = datetime.utcnow()
    value_change_30d = None
    value_change_90d = None
    value_change_1y = None

    if current_value:
        # 30 days ago
        value_30d_ago = db.query(MarketValue).filter(
            MarketValue.watch_id == watch.id,
            MarketValue.recorded_at <= now - timedelta(days=30)
        ).order_by(desc(MarketValue.recorded_at)).first()
        if value_30d_ago and value_30d_ago.currency == current_currency:
            value_change_30d = current_value - value_30d_ago.value

        # 90 days ago
        value_90d_ago = db.query(MarketValue).filter(
            MarketValue.watch_id == watch.id,
            MarketValue.recorded_at <= now - timedelta(days=90)
        ).order_by(desc(MarketValue.recorded_at)).first()
        if value_90d_ago and value_90d_ago.currency == current_currency:
            value_change_90d = current_value - value_90d_ago.value

        # 1 year ago
        value_1y_ago = db.query(MarketValue).filter(
            MarketValue.watch_id == watch.id,
            MarketValue.recorded_at <= now - timedelta(days=365)
        ).order_by(desc(MarketValue.recorded_at)).first()
        if value_1y_ago and value_1y_ago.currency == current_currency:
            value_change_1y = current_value - value_1y_ago.value

    return WatchAnalytics(
        watch_id=watch.id,
        current_value=current_value,
        current_currency=current_currency,
        purchase_price=purchase_price,
        purchase_currency=purchase_currency,
        total_return=total_return,
        roi_percentage=roi_percentage,
        annualized_return=annualized_return,
        value_change_30d=value_change_30d,
        value_change_90d=value_change_90d,
        value_change_1y=value_change_1y,
        total_valuations=total_valuations,
        first_valuation_date=first_valuation_date,
        latest_valuation_date=latest_valuation_date,
    )


