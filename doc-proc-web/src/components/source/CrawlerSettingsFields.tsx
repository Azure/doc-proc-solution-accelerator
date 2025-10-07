import { FormControl, FormField, FormItem, FormLabel, FormMessage, FormDescription } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Control, FieldPath } from "react-hook-form";
import { CRAWLER_SETTINGS_SCHEMA, CrawlerSettingSchema } from "@/lib/crawler-settings-schema";

interface CrawlerSettingsFieldsProps<T extends Record<string, any>> {
  control: Control<T>;
  fieldPrefix: FieldPath<T>;
}

interface CrawlerSettingFieldProps {
  key: string;
  schema: CrawlerSettingSchema;
  field: any;
}

export const renderCrawlerSettingField = ({ key, schema, field }: CrawlerSettingFieldProps) => {
  const { type, default: defaultValue, minimum, maximum } = schema;

  // Use existing value or default
  const currentValue = field.value !== undefined && field.value !== null ? field.value : defaultValue;

  switch (type) {
    case 'boolean':
      const boolValue = currentValue !== undefined ? currentValue : false;
      return (
        <div className="flex items-center space-x-2">
          <Switch
            checked={boolValue}
            onCheckedChange={field.onChange}
          />
          <span className="text-xs">{boolValue ? 'Yes' : 'No'}</span>
        </div>
      );

    case 'integer':
    case 'number':
      const numValue = currentValue !== undefined && currentValue !== null ? currentValue : '';
      return (
        <Input
          type="number"
          className="text-sm h-8"
          placeholder={defaultValue?.toString() || ''}
          {...field}
          onChange={(e) => {
            const val = type === 'integer' ? parseInt(e.target.value) : parseFloat(e.target.value);
            field.onChange(isNaN(val) ? undefined : val);
          }}
          min={minimum}
          max={maximum}
          value={numValue}
        />
      );

    default:
      return (
        <Input
          className="text-sm h-8"
          placeholder={`Enter ${key.replace(/_/g, ' ')}`}
          {...field}
          value={currentValue || ''}
        />
      );
  }
};

export function CrawlerSettingsFields<T extends Record<string, any>>({ 
  control, 
  fieldPrefix 
}: CrawlerSettingsFieldsProps<T>) {
  return (
    <div className="grid grid-cols-2 gap-3">
      {Object.entries(CRAWLER_SETTINGS_SCHEMA).map(([key, schema]) => (
        <FormField
          key={key}
          control={control}
          name={`${fieldPrefix}.${key}` as any}
          render={({ field }) => (
            <FormItem className="space-y-1">
              <FormLabel className="text-xs font-medium">
                {(schema as CrawlerSettingSchema).title}
              </FormLabel>
              <FormControl>
                {renderCrawlerSettingField({ key, schema: schema as CrawlerSettingSchema, field })}
              </FormControl>
              {(schema as CrawlerSettingSchema).description && (
                <FormDescription className="text-xs text-gray-500 leading-tight">
                  {(schema as CrawlerSettingSchema).description}
                </FormDescription>
              )}
              <FormMessage className="text-xs" />
            </FormItem>
          )}
        />
      ))}
    </div>
  );
}

export { CRAWLER_SETTINGS_SCHEMA };