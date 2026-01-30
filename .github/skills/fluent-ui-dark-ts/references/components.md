# Fluent UI Dark Theme Components

Wrapper components that extend **Fluent UI v9** with custom styling and behavior.

## Component Wrapper Pattern

The pattern for extending Fluent UI components:

1. **Wrap the Fluent component** with `forwardRef`
2. **Add custom props** (new appearances, behaviors)
3. **Map custom props to Fluent props** where possible
4. **Use CSS Modules** for custom styling
5. **Spread remaining props** to the underlying component

```tsx
// Pattern template
import { forwardRef } from 'react';
import { FluentComponent } from '@fluentui/react-components';
import type { FluentComponentProps } from '@fluentui/react-components';
import clsx from 'clsx';
import styles from './Component.module.css';

export interface ComponentProps extends FluentComponentProps {
  customProp?: string;
}

export const Component = forwardRef<HTMLElement, ComponentProps>(
  ({ customProp, className, ...rest }, ref) => (
    <FluentComponent
      ref={ref}
      className={clsx(styles.base, customProp && styles[customProp], className)}
      {...rest}
    />
  )
);

Component.displayName = 'Component';
```

---

## Button

Extended button with additional appearance variants:

```tsx
// components/Button/Button.tsx
import { forwardRef } from 'react';
import { Button as FluentButton, Spinner } from '@fluentui/react-components';
import type { ButtonProps as FluentButtonProps } from '@fluentui/react-components';
import clsx from 'clsx';
import styles from './Button.module.css';

export type ButtonAppearance =
  | 'primary'
  | 'secondary'
  | 'outline'
  | 'subtle'
  | 'transparent'
  | 'danger'
  | 'danger-subtle';

export interface ButtonProps extends Omit<FluentButtonProps, 'appearance'> {
  /** Button visual style */
  appearance?: ButtonAppearance;
  /** Show loading spinner and disable button */
  showLoadingSpinner?: boolean;
  /** Alignment for subtle button content */
  subtleContentAlign?: 'start' | 'center';
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      appearance = 'secondary',
      className,
      disabled,
      showLoadingSpinner,
      subtleContentAlign,
      children,
      ...rest
    },
    ref
  ) => {
    // Map custom appearances to Fluent appearances
    const fluentAppearance = (() => {
      switch (appearance) {
        case 'danger':
          return 'primary';
        case 'danger-subtle':
          return 'subtle';
        case 'outline':
          return 'outline';
        default:
          return appearance;
      }
    })();

    return (
      <FluentButton
        ref={ref}
        appearance={fluentAppearance}
        disabled={disabled || showLoadingSpinner}
        className={clsx(
          styles.button,
          appearance === 'danger' && styles.danger,
          appearance === 'danger-subtle' && styles.dangerSubtle,
          subtleContentAlign === 'start' && styles.alignStart,
          className
        )}
        {...rest}
      >
        {showLoadingSpinner && <Spinner size="tiny" />}
        {children}
      </FluentButton>
    );
  }
);

Button.displayName = 'Button';
```

```css
/* components/Button/Button.module.css */
.button {
  /* Base styles from Fluent */
}

/* Danger (destructive) button */
.danger {
  background-color: var(--colorPaletteRedBackground3);
  color: var(--colorNeutralForegroundOnBrand);
}

.danger:hover {
  background-color: var(--colorPaletteRedForeground1);
}

.danger:active {
  background-color: var(--colorPaletteRedForeground2);
}

/* Danger subtle button */
.dangerSubtle {
  color: var(--colorPaletteRedForeground1);
}

.dangerSubtle:hover {
  background-color: var(--colorPaletteRedBackground1);
  color: var(--colorPaletteRedForeground1);
}

/* Left-aligned subtle button content */
.alignStart {
  justify-content: flex-start;
}
```

### Button Usage

```tsx
// Primary action
<Button appearance="primary">Create Project</Button>

// Secondary (default)
<Button>Cancel</Button>

// Destructive action
<Button appearance="danger">Delete</Button>

// Subtle destructive
<Button appearance="danger-subtle" icon={<Delete24Regular />}>
  Remove
</Button>

// Loading state
<Button appearance="primary" showLoadingSpinner>
  Saving...
</Button>
```

---

## Input

Input with default filled-darker appearance for dark themes:

```tsx
// components/Input/Input.tsx
import { forwardRef } from 'react';
import { Input as FluentInput } from '@fluentui/react-components';
import type { InputProps as FluentInputProps } from '@fluentui/react-components';
import clsx from 'clsx';
import styles from './Input.module.css';

export interface InputProps extends FluentInputProps {}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ appearance = 'filled-darker', className, ...rest }, ref) => (
    <FluentInput
      ref={ref}
      appearance={appearance}
      className={clsx(styles.input, className)}
      {...rest}
    />
  )
);

Input.displayName = 'Input';
```

```css
/* components/Input/Input.module.css */
.input {
  /* Customize if needed */
}
```

---

## Label

Accessible label that encourages `htmlFor` usage:

```tsx
// components/Label/Label.tsx
import { forwardRef } from 'react';
import { Label as FluentLabel } from '@fluentui/react-components';
import type { LabelProps as FluentLabelProps } from '@fluentui/react-components';

export interface LabelProps extends FluentLabelProps {
  /** Associates label with form control (accessibility) */
  htmlFor?: string;
}

export const Label = forwardRef<HTMLLabelElement, LabelProps>((props, ref) => (
  <FluentLabel ref={ref} {...props} />
));

Label.displayName = 'Label';
```

---

## Field

Combined label + input with error handling:

```tsx
// components/Field/Field.tsx
import { forwardRef, useId } from 'react';
import { Field as FluentField } from '@fluentui/react-components';
import type { FieldProps as FluentFieldProps } from '@fluentui/react-components';
import clsx from 'clsx';
import styles from './Field.module.css';

export interface FieldProps extends FluentFieldProps {
  /** Show as full width */
  fullWidth?: boolean;
}

export const Field = forwardRef<HTMLDivElement, FieldProps>(
  ({ fullWidth, className, ...rest }, ref) => (
    <FluentField
      ref={ref}
      className={clsx(fullWidth && styles.fullWidth, className)}
      {...rest}
    />
  )
);

Field.displayName = 'Field';
```

```css
/* components/Field/Field.module.css */
.fullWidth {
  width: 100%;
}

.fullWidth input,
.fullWidth textarea {
  width: 100%;
}
```

### Field Usage

```tsx
<Field
  label="Project Name"
  validationMessage={errors.name?.message}
  validationState={errors.name ? 'error' : undefined}
  required
>
  <Input {...register('name')} />
</Field>
```

---

## Card

Interactive card with hover effects:

```tsx
// components/Card/Card.tsx
import { forwardRef } from 'react';
import {
  Card as FluentCard,
  CardHeader,
  CardPreview,
  Text,
} from '@fluentui/react-components';
import type { CardProps as FluentCardProps } from '@fluentui/react-components';
import clsx from 'clsx';
import styles from './Card.module.css';

export interface CardProps extends FluentCardProps {
  /** Make card clickable with hover effect */
  interactive?: boolean;
}

export const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ interactive, className, ...rest }, ref) => (
    <FluentCard
      ref={ref}
      className={clsx(
        styles.card,
        interactive && styles.interactive,
        className
      )}
      {...rest}
    />
  )
);

Card.displayName = 'Card';

// Re-export related components
export { CardHeader, CardPreview };
```

```css
/* components/Card/Card.module.css */
.card {
  background: var(--colorNeutralBackground3);
  border: 1px solid transparent;
  border-radius: var(--borderRadiusLarge);
  padding: var(--spacingXL);
}

.interactive {
  cursor: pointer;
  transition: background-color 0.15s ease, border-color 0.15s ease;
}

.interactive:hover {
  background: var(--semanticBackgroundHover);
  border-color: var(--semanticStrokeDivider);
}

.interactive:active {
  background: var(--semanticBackgroundPressed);
}
```

### Card Usage

```tsx
<Card interactive onClick={() => navigate(`/projects/${project.id}`)}>
  <CardHeader
    header={<Text weight="semibold">{project.name}</Text>}
    description={<Text size={200}>{project.description}</Text>}
    action={<Badge appearance="filled">{project.status}</Badge>}
  />
</Card>
```

---

## Badge

Status badge with semantic colors:

```tsx
// components/Badge/Badge.tsx
import { forwardRef } from 'react';
import { Badge as FluentBadge } from '@fluentui/react-components';
import type { BadgeProps as FluentBadgeProps } from '@fluentui/react-components';
import clsx from 'clsx';
import styles from './Badge.module.css';

export type BadgeStatus = 'success' | 'warning' | 'error' | 'info' | 'neutral';

export interface BadgeProps extends Omit<FluentBadgeProps, 'color'> {
  /** Semantic status color */
  status?: BadgeStatus;
}

export const Badge = forwardRef<HTMLDivElement, BadgeProps>(
  ({ status = 'neutral', className, ...rest }, ref) => {
    const colorMap: Record<BadgeStatus, FluentBadgeProps['color']> = {
      success: 'success',
      warning: 'warning',
      error: 'danger',
      info: 'informative',
      neutral: 'subtle',
    };

    return (
      <FluentBadge
        ref={ref}
        color={colorMap[status]}
        className={clsx(styles.badge, className)}
        {...rest}
      />
    );
  }
);

Badge.displayName = 'Badge';
```

```css
/* components/Badge/Badge.module.css */
.badge {
  text-transform: uppercase;
  font-size: var(--fontSizeBase100);
  font-weight: var(--fontWeightSemibold);
  letter-spacing: 0.02em;
}
```

### Badge Usage

```tsx
<Badge status="success">Active</Badge>
<Badge status="warning">Pending</Badge>
<Badge status="error">Failed</Badge>
<Badge status="info">In Progress</Badge>
<Badge status="neutral">Draft</Badge>
```

---

## Dialog

Modal dialog with standard layout:

```tsx
// components/Dialog/Dialog.tsx
import {
  Dialog as FluentDialog,
  DialogTrigger,
  DialogSurface,
  DialogTitle,
  DialogBody,
  DialogActions,
  DialogContent,
} from '@fluentui/react-components';
import type { DialogProps as FluentDialogProps } from '@fluentui/react-components';

export interface DialogProps extends FluentDialogProps {
  /** Dialog title */
  title: string;
  /** Primary action button */
  primaryAction?: React.ReactNode;
  /** Secondary action button */
  secondaryAction?: React.ReactNode;
  /** Dialog content */
  children: React.ReactNode;
}

export function Dialog({
  title,
  primaryAction,
  secondaryAction,
  children,
  ...rest
}: DialogProps) {
  return (
    <FluentDialog {...rest}>
      <DialogSurface>
        <DialogBody>
          <DialogTitle>{title}</DialogTitle>
          <DialogContent>{children}</DialogContent>
          {(primaryAction || secondaryAction) && (
            <DialogActions>
              {secondaryAction}
              {primaryAction}
            </DialogActions>
          )}
        </DialogBody>
      </DialogSurface>
    </FluentDialog>
  );
}

// Re-export trigger for convenience
export { DialogTrigger };
```

### Dialog Usage

```tsx
<Dialog
  open={isOpen}
  onOpenChange={(_, data) => setIsOpen(data.open)}
  title="Delete Project"
  primaryAction={
    <Button appearance="danger" onClick={handleDelete}>
      Delete
    </Button>
  }
  secondaryAction={
    <DialogTrigger disableButtonEnhancement>
      <Button>Cancel</Button>
    </DialogTrigger>
  }
>
  <Text>Are you sure you want to delete this project? This action cannot be undone.</Text>
</Dialog>
```

---

## Dropdown / Select

Combobox wrapper with consistent styling:

```tsx
// components/Dropdown/Dropdown.tsx
import { forwardRef } from 'react';
import {
  Dropdown as FluentDropdown,
  Option,
} from '@fluentui/react-components';
import type { DropdownProps as FluentDropdownProps } from '@fluentui/react-components';
import clsx from 'clsx';
import styles from './Dropdown.module.css';

export interface DropdownOption {
  value: string;
  label: string;
  disabled?: boolean;
}

export interface DropdownProps extends Omit<FluentDropdownProps, 'children'> {
  options: DropdownOption[];
  fullWidth?: boolean;
}

export const Dropdown = forwardRef<HTMLButtonElement, DropdownProps>(
  ({ options, fullWidth, className, ...rest }, ref) => (
    <FluentDropdown
      ref={ref}
      className={clsx(fullWidth && styles.fullWidth, className)}
      {...rest}
    >
      {options.map((option) => (
        <Option
          key={option.value}
          value={option.value}
          disabled={option.disabled}
        >
          {option.label}
        </Option>
      ))}
    </FluentDropdown>
  )
);

Dropdown.displayName = 'Dropdown';

// Re-export Option for custom usage
export { Option };
```

```css
/* components/Dropdown/Dropdown.module.css */
.fullWidth {
  width: 100%;
}
```

---

## Spinner / Loading

Centered loading indicator:

```tsx
// components/LoadingState/LoadingState.tsx
import { Spinner, Text } from '@fluentui/react-components';
import styles from './LoadingState.module.css';

export interface LoadingStateProps {
  /** Loading message */
  message?: string;
  /** Spinner size */
  size?: 'tiny' | 'extra-small' | 'small' | 'medium' | 'large' | 'extra-large' | 'huge';
}

export function LoadingState({
  message = 'Loading...',
  size = 'large',
}: LoadingStateProps) {
  return (
    <div className={styles.container}>
      <Spinner size={size} />
      {message && (
        <Text size={300} className={styles.message}>
          {message}
        </Text>
      )}
    </div>
  );
}
```

```css
/* components/LoadingState/LoadingState.module.css */
.container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--spacingM);
  padding: var(--spacingXXL);
  min-height: 200px;
}

.message {
  color: var(--colorNeutralForeground3);
}
```

---

## EmptyState

Empty content placeholder:

```tsx
// components/EmptyState/EmptyState.tsx
import type { ReactNode } from 'react';
import { Text, Button } from '@fluentui/react-components';
import styles from './EmptyState.module.css';

export interface EmptyStateProps {
  /** Icon to display */
  icon?: ReactNode;
  /** Title text */
  title: string;
  /** Description text */
  description?: string;
  /** Action button */
  action?: ReactNode;
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className={styles.container}>
      {icon && <div className={styles.icon}>{icon}</div>}
      <Text size={500} weight="semibold" className={styles.title}>
        {title}
      </Text>
      {description && (
        <Text size={300} className={styles.description}>
          {description}
        </Text>
      )}
      {action && <div className={styles.action}>{action}</div>}
    </div>
  );
}
```

```css
/* components/EmptyState/EmptyState.module.css */
.container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--spacingM);
  padding: var(--spacingXXXL);
  text-align: center;
  min-height: 300px;
}

.icon {
  font-size: 48px;
  color: var(--colorNeutralForeground4);
  margin-bottom: var(--spacingS);
}

.title {
  color: var(--colorNeutralForeground1);
}

.description {
  color: var(--colorNeutralForeground3);
  max-width: 400px;
}

.action {
  margin-top: var(--spacingM);
}
```

### EmptyState Usage

```tsx
<EmptyState
  icon={<Folder24Regular />}
  title="No projects yet"
  description="Create your first project to get started."
  action={
    <Button appearance="primary" icon={<Add24Regular />}>
      Create Project
    </Button>
  }
/>
```

---

## Component Index

Export all components from a central index:

```tsx
// components/index.ts
export { Button } from './Button/Button';
export type { ButtonProps, ButtonAppearance } from './Button/Button';

export { Input } from './Input/Input';
export type { InputProps } from './Input/Input';

export { Label } from './Label/Label';
export type { LabelProps } from './Label/Label';

export { Field } from './Field/Field';
export type { FieldProps } from './Field/Field';

export { Card, CardHeader, CardPreview } from './Card/Card';
export type { CardProps } from './Card/Card';

export { Badge } from './Badge/Badge';
export type { BadgeProps, BadgeStatus } from './Badge/Badge';

export { Dialog, DialogTrigger } from './Dialog/Dialog';
export type { DialogProps } from './Dialog/Dialog';

export { Dropdown, Option } from './Dropdown/Dropdown';
export type { DropdownProps, DropdownOption } from './Dropdown/Dropdown';

export { LoadingState } from './LoadingState/LoadingState';
export type { LoadingStateProps } from './LoadingState/LoadingState';

export { EmptyState } from './EmptyState/EmptyState';
export type { EmptyStateProps } from './EmptyState/EmptyState';

// Re-export commonly used Fluent components
export {
  Text,
  Spinner,
  Tooltip,
  Menu,
  MenuItem,
  MenuList,
  MenuPopover,
  MenuTrigger,
  Divider,
  Avatar,
  Persona,
  ProgressBar,
  Switch,
  Checkbox,
  Radio,
  RadioGroup,
  Textarea,
  DataGrid,
  DataGridHeader,
  DataGridRow,
  DataGridHeaderCell,
  DataGridBody,
  DataGridCell,
  createTableColumn,
  TabList,
  Tab,
} from '@fluentui/react-components';
```

---

## Spacing Quick Reference

| Component | Padding | Gap |
|-----------|---------|-----|
| Card | `--spacingXL` (20px) | - |
| Dialog body | `--spacingXL` (20px) | `--spacingL` (16px) |
| Form fields | - | `--spacingL` (16px) |
| Button group | - | `--spacingS` (8px) |
| Badge/Tag | `--spacingXXS` / `--spacingS` | - |
| Empty state | `--spacingXXXL` (32px) | `--spacingM` (12px) |
