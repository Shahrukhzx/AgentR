import { Switch } from '@headlessui/react';
import { cn } from '@/lib/utils';

interface ToggleSwitchProps {
  enabled: boolean;
  onChange: (value: boolean) => void;
  label: string;
  description?: string;
  hideDescription?: boolean;
}

export function ToggleSwitch({ 
  enabled, 
  onChange, 
  label, 
  description, 
  hideDescription = true 
}: ToggleSwitchProps) {
  return (
    <Switch.Group>
      <div className="flex items-center space-x-3">
        <Switch
          checked={enabled}
          onChange={onChange}
          className={cn(
            enabled ? 'bg-indigo-500' : 'bg-zinc-700',
            'relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-black'
          )}
        >
          <span
            className={cn(
              enabled ? 'translate-x-6' : 'translate-x-1',
              'inline-block h-4 w-4 transform rounded-full bg-white transition-transform'
            )}
          />
        </Switch>
        <div className="flex flex-col">
          {label && <Switch.Label className="text-sm font-medium text-zinc-200">{label}</Switch.Label>}
          {description && !hideDescription && (
            <Switch.Description className="text-xs text-zinc-400">
              {description}
            </Switch.Description>
          )}
        </div>
      </div>
    </Switch.Group>
  );
} 