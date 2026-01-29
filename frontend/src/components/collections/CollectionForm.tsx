import { useForm } from 'react-hook-form'
import Input from '@/components/common/Input'
import Button from '@/components/common/Button'
import type { Collection, CollectionCreate, CollectionUpdate } from '@/types'

interface CollectionFormProps {
  defaultValues?: Collection
  onSubmit: (data: CollectionCreate | CollectionUpdate) => void
  onCancel: () => void
  isLoading?: boolean
}

const colorOptions = [
  { value: '#3B82F6', label: 'Blue', class: 'bg-blue-500' },
  { value: '#10B981', label: 'Green', class: 'bg-green-500' },
  { value: '#EF4444', label: 'Red', class: 'bg-red-500' },
  { value: '#F59E0B', label: 'Yellow', class: 'bg-yellow-500' },
  { value: '#8B5CF6', label: 'Purple', class: 'bg-purple-500' },
  { value: '#EC4899', label: 'Pink', class: 'bg-pink-500' },
  { value: '#6366F1', label: 'Indigo', class: 'bg-indigo-500' },
  { value: '#6B7280', label: 'Gray', class: 'bg-gray-500' },
]

export default function CollectionForm({
  defaultValues,
  onSubmit,
  onCancel,
  isLoading,
}: CollectionFormProps) {
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<CollectionCreate | CollectionUpdate>({
    defaultValues: defaultValues || {
      color: '#3B82F6',
    },
  })

  const selectedColor = watch('color')

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <Input
        label="Collection Name"
        required
        {...register('name', { required: 'Collection name is required' })}
        error={errors.name?.message}
        placeholder="e.g., Current Collection, Wishlist, Sold"
      />

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Description
        </label>
        <textarea
          {...register('description')}
          rows={3}
          className="block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          placeholder="Optional description of this collection..."
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Color <span className="text-red-500">*</span>
        </label>
        <div className="grid grid-cols-4 gap-3">
          {colorOptions.map((color) => (
            <label
              key={color.value}
              className={`relative flex items-center justify-center h-12 rounded-md cursor-pointer border-2 ${
                selectedColor === color.value
                  ? 'border-gray-900 ring-2 ring-gray-900 ring-offset-2'
                  : 'border-gray-300 hover:border-gray-400'
              }`}
            >
              <input
                type="radio"
                value={color.value}
                {...register('color', { required: 'Color is required' })}
                className="sr-only"
              />
              <div className={`w-8 h-8 rounded-full ${color.class}`} />
              <span className="sr-only">{color.label}</span>
            </label>
          ))}
        </div>
        {errors.color && (
          <p className="mt-1 text-sm text-red-600">{errors.color.message}</p>
        )}
      </div>

      <div className="flex gap-3 pt-4">
        <Button type="submit" disabled={isLoading} className="flex-1">
          {isLoading ? 'Saving...' : defaultValues ? 'Update Collection' : 'Create Collection'}
        </Button>
        <Button type="button" variant="secondary" onClick={onCancel} disabled={isLoading}>
          Cancel
        </Button>
      </div>
    </form>
  )
}
