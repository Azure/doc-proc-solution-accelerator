import { FormControl, FormField, FormItem, FormLabel, FormMessage, FormDescription } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Control, FieldPath } from "react-hook-form";
import { SourceSettingsSchema } from "@/lib/api";

interface SourceSettingsFieldsProps<T extends Record<string, any>> {
  control: Control<T>;
  fieldPrefix: FieldPath<T>;
  settingsSchema?: Record<string, SourceSettingsSchema>;
  fallbackToJson?: boolean;
}

interface SourceSettingFieldProps {
  key: string;
  schema: SourceSettingsSchema;
  field: any;
}

export const renderSourceSettingField = ({ key, schema, field }: SourceSettingFieldProps) => {
  const { type, enum: enumValues, sensitive, default: defaultValue } = schema;

  // Set default value if not already set
  if ((field.value === undefined || field.value === null) && defaultValue !== undefined && defaultValue !== null) {
    field.onChange(defaultValue);
  }

  switch (type) {
    case 'boolean':
      const boolValue = field.value !== undefined ? field.value : (defaultValue !== undefined ? defaultValue : false);
      return (
        <div className="flex items-center space-x-2">
          <Switch
            checked={boolValue}
            onCheckedChange={field.onChange}
          />
          <span className="text-sm">{boolValue ? 'Enabled' : 'Disabled'}</span>
        </div>
      );

    case 'integer':
    case 'number':
      const numValue = field.value !== undefined && field.value !== null ? field.value : (defaultValue !== undefined ? defaultValue : '');
      return (
        <Input
          type="number"
          placeholder={`Enter ${key.replace(/_/g, ' ')}`}
          {...field}
          onChange={(e) => {
            const val = type === 'integer' ? parseInt(e.target.value) : parseFloat(e.target.value);
            field.onChange(isNaN(val) ? undefined : val);
          }}
          min={schema.minimum}
          max={schema.maximum}
          value={numValue}
        />
      );

    case 'string':
      if (enumValues && enumValues.length > 0) {
        const selectValue = field.value !== undefined ? field.value : (defaultValue !== undefined ? defaultValue : '');
        return (
          <Select onValueChange={field.onChange} value={selectValue}>
            <SelectTrigger>
              <SelectValue placeholder={`Select ${key.replace(/_/g, ' ')}`} />
            </SelectTrigger>
            <SelectContent>
              {enumValues.map((value: any) => (
                <SelectItem key={value} value={value}>
                  {value}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        );
      }

      const stringValue = field.value !== undefined ? field.value : (defaultValue !== undefined ? defaultValue : '');
      return (
        <Input
          type={sensitive ? "password" : "text"}
          placeholder={`Enter ${key.replace(/_/g, ' ')}`}
          {...field}
          value={stringValue}
        />
      );

    default:
      return (
        <Input
          placeholder={`Enter ${key.replace(/_/g, ' ')}`}
          {...field}
          value={field.value || ''}
        />
      );
  }
};

export function SourceSettingsFields<T extends Record<string, any>>({ 
  control, 
  fieldPrefix,
  settingsSchema,
  fallbackToJson = false
}: SourceSettingsFieldsProps<T>) {
  // If no schema is available and fallback is enabled, show JSON textarea
  if (!settingsSchema && fallbackToJson) {
    return (
      <FormField
        control={control}
        name={fieldPrefix as any}
        render={({ field }) => (
          <FormItem>
            <FormLabel>Settings (JSON)</FormLabel>
            <FormControl>
              <Textarea
                placeholder="Enter configuration as JSON..."
                className="min-h-[120px]"
                value={JSON.stringify(field.value || {}, null, 2)}
                onChange={(e) => {
                  try {
                    const parsed = JSON.parse(e.target.value);
                    field.onChange(parsed);
                  } catch {
                    // Keep the text value for now
                  }
                }}
              />
            </FormControl>
            <FormDescription>
              Configuration settings for this source instance
            </FormDescription>
            <FormMessage />
          </FormItem>
        )}
      />
    );
  }

  // If no schema is available and no fallback, return null
  if (!settingsSchema) {
    return null;
  }

  // Render fields based on schema
  return (
    <div className="space-y-4">
      {Object.entries(settingsSchema).map(([key, schema]) => (
        <FormField
          key={key}
          control={control}
          name={`${fieldPrefix}.${key}` as any}
          rules={{ 
            required: schema.required ? `${schema.title || key} is required` : false 
          }}
          render={({ field }) => (
            <FormItem>
              <FormLabel className="capitalize">
                {schema.title || key.replace(/_/g, ' ')}
                {schema.required && <span className="text-red-500 ml-1">*</span>}
              </FormLabel>
              <FormControl>
                {renderSourceSettingField({ key, schema, field })}
              </FormControl>
              {schema.description && (
                <FormDescription className="text-xs text-gray-500">{schema.description}</FormDescription>
              )}
              <FormMessage />
            </FormItem>
          )}
        />
      ))}
    </div>
  );
}