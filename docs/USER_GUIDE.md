# Watch Collection Tracker - User Guide

Welcome to the Watch Collection Tracker! This guide will help you get started with managing your watch collection.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Managing Watches](#managing-watches)
3. [Collections](#collections)
4. [Images](#images)
5. [Service History](#service-history)
6. [Market Values & Analytics](#market-values--analytics)
7. [Watch Comparison](#watch-comparison)
8. [Watch Setting Tool](#watch-setting-tool)
9. [Tips & Best Practices](#tips--best-practices)

---

## Getting Started

### Registration

1. Navigate to http://localhost:8080
2. Click "Register" in the navigation bar
3. Enter your email address and password
4. Click "Create Account"
5. You'll be automatically logged in

### Login

1. Navigate to http://localhost:8080
2. Click "Login" in the navigation bar
3. Enter your email and password
4. Click "Sign In"

### Dashboard

After logging in, you'll see the dashboard with:
- **Total Watches**: Count of watches in your collection
- **Total Value**: Combined current market value
- **Quick Stats**: ROI, recent additions, service due
- **Recent Watches**: Your most recently added watches

---

## Managing Watches

### Adding a Watch

1. Click "Watches" in the navigation bar
2. Click the "Add Watch" button
3. Fill in the watch details:
   - **Model** (required): The watch model name (e.g., "Submariner Date")
   - **Brand** (required): Select from the dropdown
   - **Collection**: Optionally assign to a collection
   - **Reference Number**: Official reference (e.g., "116610LN")
   - **Serial Number**: Watch serial number
   - **Movement Type**: Automatic, Manual, Quartz, etc.
   - **Case Material**: Stainless Steel, Gold, Titanium, etc.
   - **Case Diameter**: Size in millimeters
   - **Water Resistance**: Depth rating in meters
   - **Purchase Date**: When you acquired the watch
   - **Purchase Price**: What you paid
   - **Purchase Currency**: USD, EUR, GBP, etc.
   - **Condition**: Mint, Excellent, Good, Fair, Poor
   - **Notes**: Any additional information

4. Click "Add Watch" to save

### Viewing Watches

**List View**:
- View all your watches in a grid layout
- Each card shows:
  - Primary image (if uploaded)
  - Brand and model
  - Collection (color-coded)
  - Purchase price
  - Purchase date
  - Condition badge

**Detail View**:
- Click any watch card to see full details
- Includes all specifications, images, service history, and analytics

### Searching & Filtering

**Search**:
- Use the search bar to find watches by:
  - Model name
  - Brand name
  - Reference number
  - Serial number

**Filters**:
- **Brand**: Filter by specific manufacturer
- **Collection**: Show watches from a specific collection
- **Condition**: Filter by condition rating
- **Price Range**: Set minimum and maximum values
- **Date Range**: Filter by purchase date

**Sorting**:
- Sort by:
  - Created date (newest/oldest)
  - Purchase date
  - Purchase price
  - Model name (A-Z)

### Editing Watches

1. Navigate to the watch detail page
2. Click "Edit" button
3. Update any fields
4. Click "Save Changes"

### Deleting Watches

1. Navigate to the watch detail page
2. Click "Delete" button
3. Confirm deletion
4. **Note**: This will also delete all associated images, service records, and market values

---

## Collections

Collections help you organize your watches into groups (e.g., "Dive Watches", "Dress Watches", "Vintage").

### Creating a Collection

1. Click "Collections" in the navigation bar
2. Click "New Collection"
3. Enter:
   - **Name**: Collection name (e.g., "Dive Watches")
   - **Description**: Optional description
   - **Color**: Pick a color for visual identification
4. Click "Create Collection"

### Managing Collections

**View Collections**:
- See all your collections with watch counts
- Color-coded badges for easy identification

**Edit Collection**:
- Click "Edit" on any collection
- Update name, description, or color
- Click "Save"

**Delete Collection**:
- Click "Delete" on any collection
- Confirm deletion
- **Note**: Watches are NOT deleted, only unassigned

### Assigning Watches to Collections

**During Watch Creation**:
- Select collection from dropdown when adding a watch

**For Existing Watches**:
1. Edit the watch
2. Select collection from dropdown
3. Save changes

---

## Images

Upload and manage photos of your watches.

### Uploading Images

1. Navigate to watch detail page
2. Scroll to "Images" section
3. **Drag & Drop**:
   - Drag image files directly onto the upload area
   - Or click "Select files" to browse

**Supported Formats**:
- JPG, PNG, GIF, WebP
- Maximum size: 20MB per image
- Automatically extracts dimensions

### Managing Images

**Primary Image**:
- The first uploaded image becomes the primary image
- Primary image shows on watch cards and thumbnails
- Click "Set as Primary" on any image to change

**Image Gallery**:
- View all images in grid layout
- Click image to view full-screen
- Use arrow keys to navigate

**Deleting Images**:
- Click "Delete" on any image
- Confirm deletion
- If deleting primary image, next image auto-promotes

### Full-Screen Lightbox

- Click any image to view full-screen
- **Keyboard shortcuts**:
  - `←` / `→` - Navigate between images
  - `ESC` - Close lightbox

---

## Service History

Track maintenance and service records for each watch.

### Adding Service Records

1. Navigate to watch detail page
2. Scroll to "Service History" section
3. Click "Add Service Record"
4. Fill in details:
   - **Service Date** (required): When service was performed
   - **Provider** (required): Shop/center name
   - **Service Type**: Full Service, Regulation, Polishing, etc.
   - **Description**: Details about work performed
   - **Cost**: Service cost
   - **Currency**: USD, EUR, GBP, etc.
   - **Next Service Due**: When next service is recommended
5. Click "Add Record"

### Uploading Service Documents

1. Find the service record in the timeline
2. Click "Upload Document"
3. Select file:
   - PDF, JPG, PNG supported
   - Maximum size: 10MB
4. Documents appear with download links

**Document Types**:
- Service receipts
- Warranty certificates
- Authentication papers
- Polishing reports

### Service Timeline

Service records display in chronological order (most recent first):
- **Date** and **Provider** displayed prominently
- **Service Type** and **Cost** shown
- **Overdue Alert**: Red indicator if next service is overdue
- **Documents**: Expandable section with download links

### Editing Service Records

1. Click "Edit" on any service record
2. Update details
3. Click "Save"

### Deleting Service Records

1. Click "Delete" on any service record
2. Confirm deletion
3. **Note**: Also deletes associated documents

---

## Market Values & Analytics

Track your watch's value over time and view performance analytics.

### Adding Market Values

1. Navigate to watch detail page
2. Scroll to "Market Values" section
3. Click "Add Market Value"
4. Enter:
   - **Value** (required): Current market value
   - **Currency**: USD, EUR, GBP, CHF, JPY, AUD, CAD
   - **Source**: Manual, Chrono24, API
   - **Recorded At**: Date of valuation (defaults to now)
   - **Notes**: Optional context
5. Click "Add Value"

**Tips**:
- Add values regularly to track trends
- Historical values can be added with past dates
- Only the most recent value updates the watch's current value

### Watch Analytics

Each watch displays performance metrics:

**ROI (Return on Investment)**:
- Percentage gain/loss since purchase
- Color-coded: Green (profit), Red (loss)

**Total Return**:
- Absolute dollar amount gained/lost

**Annualized Return**:
- Time-adjusted performance percentage

**Value Changes**:
- 30-day change
- 90-day change
- 1-year change

**Value Chart**:
- Line chart showing value over time
- Hover for specific values
- Visual trend identification

### Collection Analytics

View your entire collection's performance:

1. Click "Analytics" in navigation bar
2. Select currency (USD, EUR, GBP, etc.)
3. View:
   - **Total Collection Value**
   - **Average ROI**
   - **Top Performers** (highest ROI)
   - **Worst Performers** (lowest ROI)
   - **Value by Brand** (bar chart)
   - **Collection Distribution** (pie chart)
   - **Brand Performance Table**

**Key Metrics**:
- Total watches count
- Total purchase price
- Total current value
- Total return (profit/loss)
- Average ROI across collection

---

## Watch Comparison

Compare multiple watches side-by-side to help make purchase decisions or analyze your collection.

### Selecting Watches for Comparison

1. Go to "Watches" page
2. Click "Compare" button to enter compare mode
3. **Select watches**:
   - Checkboxes appear on watch cards
   - Click to select (2-4 watches required)
   - Selected watches have blue border
4. **Comparison bar** shows count and actions

### Viewing Comparison

1. Click "Compare Selected" in the comparison bar
2. See side-by-side comparison table with:
   - **Images**: Primary images
   - **Basic Info**: Brand, model, reference
   - **Purchase Info**: Date, price, currency, condition
   - **Specifications**: Case material, diameter, water resistance
   - **Movement**: Movement type, complications
   - **Market Value**: Current value, ROI, gain/loss
   - **Service History**: Last service, next due

**Color Coding**:
- Green: Positive ROI
- Red: Negative ROI
- Gray: N/A (missing data)

### Removing from Comparison

- Click "Remove" under any watch column
- Updates comparison in real-time

### Sharing Comparisons

The comparison URL can be shared:
```
/compare?ids=id1,id2,id3
```

Anyone with the link (and access) can view the comparison.

---

## Watch Setting Tool

Use the time reference to set your watches accurately.

1. Click "Settings" in navigation bar
2. See current time display (updates every second)
3. **Use for setting**:
   - Pull crown to position
   - Wait for second hand to reach 12
   - When display changes to next minute, push crown in
   - Watch is now synchronized

**Tips**:
- Use for mechanical watches requiring precise setting
- Especially useful for chronometers
- Reference is synchronized to system time

---

## Tips & Best Practices

### Photography Tips

**Good Photos**:
- Use natural lighting (near window)
- Clean watch before photographing
- Multiple angles: face, profile, case back, clasp
- Include original box and papers if available
- White background preferred

### Service Tracking

**Recommendations**:
- Add service records immediately after service
- Upload receipts and certificates for warranty
- Set next service due dates (typically 5-7 years)
- Track small maintenance (battery changes, strap replacements)

### Market Value Tracking

**Best Practices**:
- Update values quarterly or semi-annually
- Use consistent sources (e.g., always Chrono24)
- Note market conditions in notes field
- Compare against similar condition/year watches

### Data Organization

**Collections**:
- Use logical groupings (by style, brand, era)
- Color-code by category (blue = dive, brown = dress, etc.)
- Keep collections focused (5-15 watches per collection)

**Notes Field**:
- Document unique features or history
- Record provenance if significant
- Note any modifications or customizations
- Include story of acquisition

### Search Efficiency

**Use Filters**:
- Combine multiple filters for precise results
- Save common filter combinations (upcoming feature)

**Search Tips**:
- Use partial terms (e.g., "sub" finds "Submariner")
- Brand names are searchable
- Reference numbers are exact match

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `/` | Focus search bar |
| `ESC` | Close modals/lightbox |
| `←` / `→` | Navigate images in lightbox |
| `n` | New watch (from watches page) |
| `c` | New collection (from collections page) |

---

## Mobile Usage

The application is responsive and works on mobile devices:

**Optimizations**:
- Touch-friendly buttons and controls
- Swipe navigation in image gallery
- Mobile-optimized forms
- Responsive tables and charts

**Best Practices**:
- Use mobile for viewing and light edits
- Desktop recommended for bulk uploads
- Photo upload works great from mobile camera

---

## Data Export

**Current Export Options**:
- All data accessible via API
- Screenshots for sharing
- Print-friendly watch details

**Future Features**:
- CSV export
- PDF reports
- Insurance documentation

---

## Privacy & Security

**Your Data**:
- All data is private to your account
- Watch images stored securely
- Passwords hashed with bcrypt
- JWT tokens for authentication

**Best Practices**:
- Use strong, unique password
- Log out on shared devices
- Don't share access tokens
- Regular password updates recommended

---

## Troubleshooting

**Can't Upload Images**:
- Check file size (<20MB)
- Verify file format (JPG, PNG, GIF, WebP)
- Try different browser if issues persist

**Search Not Working**:
- Clear filters
- Try broader search terms
- Verify spelling

**Analytics Not Showing**:
- Ensure market values are added
- Check currency matches
- Requires purchase price for ROI

**Slow Performance**:
- Clear browser cache
- Reduce number of displayed items
- Close unused browser tabs

---

## Getting Help

**Support Options**:
- GitHub Issues: https://github.com/Homoney/watch_collection_tracker/issues
- Email: support@example.com (if configured)
- Check API documentation: http://localhost:8080/api/docs

**Reporting Bugs**:
- Include browser and version
- Describe steps to reproduce
- Screenshots if applicable
- Check console for errors (F12)

---

## What's Next?

**Upcoming Features**:
- Insurance value reports
- Watchlist/wish list
- Price alerts
- Chrono24 API integration
- Mobile app
- Public sharing
- QR codes for watches

Stay tuned for updates!

---

**Last Updated**: 2026-01-28
**Version**: 1.0.0
