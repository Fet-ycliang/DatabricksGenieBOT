---
name: fluent-ui-dark-ts
description: Build dark-themed React applications using Fluent UI v9 with custom theming, wrapper components, and page templates. Use when creating dashboards, admin panels, or data-rich interfaces with a refined dark aesthetic.
---

# Fluent UI Dark Theme System

A production-ready dark theme design system built on **Fluent UI v9** (`@fluentui/react-components`).

## Stack

```json
{
  "dependencies": {
    "@fluentui/react-components": "^9.x",
    "@fluentui/react-icons": "^2.x",
    "clsx": "^2.x",
    "react": "^18.x",
    "react-router-dom": "^6.x"
  }
}
```

## Theme Setup

### 1. Create Brand Variants

```typescript
// theme/brand.ts
import type { BrandVariants } from '@fluentui/react-components';

// Purple-based brand (adjust hue for your brand)
export const brandVariants: BrandVariants = {
  10: '#030206',
  20: '#1A1326',
  30: '#2B1D44',
  40: '#38255E',
  50: '#472E79',
  60: '#553695',
  70: '#643FB2',
  80: '#8251EE',  // Primary brand color
  90: '#8251EE',
  100: '#9263F1',
  110: '#A175F3',
  120: '#AF86F5',
  130: '#BC98F7',
  140: '#C9AAF9',
  150: '#D5BCFB',
  160: '#E1CEFC',
};
```

### 2. Create Dark Theme with Custom Overrides

```typescript
// theme/dark-theme.ts
import { createDarkTheme, createLightTheme } from '@fluentui/react-components';
import type { Theme } from '@fluentui/react-components';
import { brandVariants } from './brand';

// Custom neutral backgrounds using HSL for better dark theme contrast
const neutralBackgroundOverrides = {
  colorNeutralBackground1: 'hsl(240, 6%, 10%)',   // Base background
  colorNeutralBackground2: 'hsl(240, 5%, 12%)',   // Elevated surfaces
  colorNeutralBackground3: 'hsl(240, 5%, 14%)',   // Cards, panels
  colorNeutralBackground4: 'hsl(240, 4%, 18%)',   // Borders, dividers
  colorNeutralBackground5: 'hsl(240, 4%, 22%)',   // Hover states
  colorNeutralBackground6: 'hsl(240, 4%, 26%)',   // Active states
};

// Font family (optional - use system fonts or custom)
const fontFamilyTokens = {
  fontFamilyBase: "'Aptos', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
  fontFamilyMonospace: "'Cascadia Code', 'Fira Code', Consolas, monospace",
};

// Data visualization colors for charts
const dataVizTokens = {
  dataViz1: '#8251EE',  // Primary purple
  dataViz2: '#3B82F6',  // Blue
  dataViz3: '#10B981',  // Green
  dataViz4: '#F59E0B',  // Amber
  dataViz5: '#EF4444',  // Red
  dataViz6: '#EC4899',  // Pink
  dataViz7: '#06B6D4',  // Cyan
};

export const darkTheme: Theme = {
  ...createDarkTheme(brandVariants),
  ...neutralBackgroundOverrides,
  ...fontFamilyTokens,
  ...dataVizTokens,
};

export const lightTheme: Theme = {
  ...createLightTheme(brandVariants),
  ...fontFamilyTokens,
  ...dataVizTokens,
};
```

### 3. Apply Theme with FluentProvider

```tsx
// App.tsx
import { FluentProvider } from '@fluentui/react-components';
import { darkTheme } from './theme/dark-theme';

export function App() {
  return (
    <FluentProvider theme={darkTheme}>
      <YourApp />
    </FluentProvider>
  );
}
```

## CSS Variables

Add these custom CSS variables inside the FluentProvider scope:

```css
/* styles/tokens.css */
.fui-FluentProvider {
  /* Spacing scale */
  --spacingNone: 0;
  --spacingXXS: 2px;
  --spacingXS: 4px;
  --spacingSNudge: 6px;
  --spacingS: 8px;
  --spacingMNudge: 10px;
  --spacingM: 12px;
  --spacingL: 16px;
  --spacingXL: 20px;
  --spacingXXL: 24px;
  --spacingXXXL: 32px;
  --spacingPagePadding: var(--spacingXXL);

  /* Extended border radius */
  --borderRadiusXXLarge: 12px;
  --borderRadiusXXXLarge: 24px;

  /* Content width constraints */
  --contentWidthXS: 320px;
  --contentWidthS: 480px;
  --contentWidthM: 640px;
  --contentWidthL: 960px;
  --contentWidthXL: 1280px;

  /* Semantic background aliases */
  --semanticBackground1: var(--colorNeutralBackground1);
  --semanticBackground2: var(--colorNeutralBackground2);
  --semanticBackground3: var(--colorNeutralBackground3);
  --semanticBackground4: var(--colorNeutralBackground4);
  --semanticStrokeDivider: var(--semanticBackground4);

  /* Interactive state colors */
  --semanticBackgroundHover: hsl(0deg 0% 50% / 10%);
  --semanticBackgroundPressed: hsl(0deg 0% 0% / 40%);
  --semanticBackgroundSelected: hsl(0deg 0% 50% / 15%);
}

@media (max-width: 640px) {
  .fui-FluentProvider {
    --spacingPagePadding: var(--spacingL);
  }
}
```

## Component Wrapper Pattern

Extend Fluent UI components with custom variants using CSS Modules:

### Button with Custom Appearances

```tsx
// components/Button/Button.tsx
import { forwardRef } from 'react';
import { Button as FluentButton } from '@fluentui/react-components';
import type { ButtonProps as FluentButtonProps } from '@fluentui/react-components';
import clsx from 'clsx';
import styles from './Button.module.css';

export type ButtonAppearance = 
  | 'primary' 
  | 'secondary' 
  | 'danger' 
  | 'danger-subtle' 
  | 'subtle' 
  | 'transparent';

export interface ButtonProps extends Omit<FluentButtonProps, 'appearance'> {
  appearance?: ButtonAppearance;
  showLoadingSpinner?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ appearance = 'secondary', className, disabled, showLoadingSpinner, children, ...rest }, ref) => {
    const fluentAppearance = appearance === 'danger' || appearance === 'danger-subtle' 
      ? (appearance === 'danger' ? 'primary' : 'subtle')
      : appearance;

    return (
      <FluentButton
        ref={ref}
        appearance={fluentAppearance}
        className={clsx(
          styles.button,
          appearance === 'danger' && styles.danger,
          appearance === 'danger-subtle' && styles.dangerSubtle,
          className
        )}
        disabled={disabled || showLoadingSpinner}
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
  /* Base styles inherited from Fluent */
}

.danger {
  background-color: var(--colorPaletteRedBackground3);
  color: var(--colorNeutralForegroundOnBrand);
}

.danger:hover {
  background-color: var(--colorPaletteRedForeground1);
}

.dangerSubtle {
  color: var(--colorPaletteRedForeground1);
}

.dangerSubtle:hover {
  background-color: var(--colorPaletteRedBackground1);
}
```

### Input with Default Appearance

```tsx
// components/Input/Input.tsx
import { forwardRef } from 'react';
import { Input as FluentInput } from '@fluentui/react-components';
import type { InputProps as FluentInputProps } from '@fluentui/react-components';

export interface InputProps extends FluentInputProps {}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ appearance = 'filled-darker', ...rest }, ref) => (
    <FluentInput ref={ref} appearance={appearance} {...rest} />
  )
);

Input.displayName = 'Input';
```

### Accessible Label

```tsx
// components/Label/Label.tsx
import { forwardRef } from 'react';
import { Label as FluentLabel } from '@fluentui/react-components';
import type { LabelProps as FluentLabelProps } from '@fluentui/react-components';

export interface LabelProps extends FluentLabelProps {
  htmlFor?: string;  // Encourage accessibility
}

export const Label = forwardRef<HTMLLabelElement, LabelProps>((props, ref) => (
  <FluentLabel ref={ref} {...props} />
));

Label.displayName = 'Label';
```

## Page Templates

### BasicPage - Standard Page Layout

```tsx
// components/BasicPage/BasicPage.tsx
import type { ReactNode } from 'react';
import { Button } from '@fluentui/react-components';
import { ArrowLeft24Regular } from '@fluentui/react-icons';
import clsx from 'clsx';
import styles from './BasicPage.module.css';

export interface BasicPageProps {
  title?: string;
  titleIcon?: ReactNode;
  action?: ReactNode;
  onGoBack?: () => void;
  scrollMode?: 'page' | 'content';
  preContent?: ReactNode;
  children: ReactNode;
  className?: string;
}

export function BasicPage({
  title,
  titleIcon,
  action,
  onGoBack,
  scrollMode = 'page',
  preContent,
  children,
  className,
}: BasicPageProps) {
  return (
    <div className={clsx(styles.page, styles[scrollMode], className)}>
      {preContent}
      
      {(title || action || onGoBack) && (
        <header className={styles.header}>
          <div className={styles.titleRow}>
            {onGoBack && (
              <Button
                appearance="subtle"
                icon={<ArrowLeft24Regular />}
                onClick={onGoBack}
                aria-label="Go back"
              />
            )}
            {titleIcon}
            {title && <h1 className={styles.title}>{title}</h1>}
          </div>
          {action && <div className={styles.actions}>{action}</div>}
        </header>
      )}

      <main className={styles.content}>{children}</main>
    </div>
  );
}
```

```css
/* components/BasicPage/BasicPage.module.css */
.page {
  display: flex;
  flex-direction: column;
  min-height: 100%;
  padding: var(--spacingPagePadding);
}

.page.page {
  overflow-y: auto;
}

.content {
  overflow-y: auto;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacingM);
  margin-bottom: var(--spacingXL);
  flex-shrink: 0;
}

.titleRow {
  display: flex;
  align-items: center;
  gap: var(--spacingS);
}

.title {
  font-size: var(--fontSizeHero800);
  font-weight: var(--fontWeightSemibold);
  line-height: var(--lineHeightHero800);
  margin: 0;
}

.content {
  flex: 1;
}
```

### TabsPage - In-Page Tabs (No Routing)

```tsx
// components/TabsPage/TabsPage.tsx
import { useState } from 'react';
import { TabList, Tab } from '@fluentui/react-components';
import type { SelectTabData } from '@fluentui/react-components';
import { BasicPage, type BasicPageProps } from '../BasicPage/BasicPage';
import styles from './TabsPage.module.css';

export interface TabDefinition {
  id: string;
  label: string;
  icon?: ReactNode;
  content: ReactNode;
}

export interface TabsPageProps extends Omit<BasicPageProps, 'children'> {
  tabs: TabDefinition[];
  defaultTab?: string;
}

export function TabsPage({ tabs, defaultTab, ...pageProps }: TabsPageProps) {
  const [selectedTab, setSelectedTab] = useState(defaultTab ?? tabs[0]?.id);

  const handleTabSelect = (_: unknown, data: SelectTabData) => {
    setSelectedTab(data.value as string);
  };

  const activeTab = tabs.find((t) => t.id === selectedTab);

  return (
    <BasicPage {...pageProps}>
      <TabList
        selectedValue={selectedTab}
        onTabSelect={handleTabSelect}
        className={styles.tabList}
      >
        {tabs.map((tab) => (
          <Tab key={tab.id} value={tab.id} icon={tab.icon}>
            {tab.label}
          </Tab>
        ))}
      </TabList>

      <div className={styles.tabContent}>{activeTab?.content}</div>
    </BasicPage>
  );
}
```

### TabNavPage - Tabs with Routing

```tsx
// components/TabNavPage/TabNavPage.tsx
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { TabList, Tab } from '@fluentui/react-components';
import { BasicPage, type BasicPageProps } from '../BasicPage/BasicPage';
import styles from './TabNavPage.module.css';

export interface TabNavDefinition {
  id: string;
  label: string;
  path: string;
  icon?: ReactNode;
}

export interface TabNavPageProps extends Omit<BasicPageProps, 'children'> {
  tabs: TabNavDefinition[];
  basePath: string;
}

export function TabNavPage({ tabs, basePath, ...pageProps }: TabNavPageProps) {
  const location = useLocation();
  
  const selectedTab = tabs.find((t) => 
    location.pathname.startsWith(`${basePath}/${t.path}`)
  )?.id ?? tabs[0]?.id;

  return (
    <BasicPage {...pageProps}>
      <TabList selectedValue={selectedTab} className={styles.tabList}>
        {tabs.map((tab) => (
          <Tab
            key={tab.id}
            value={tab.id}
            icon={tab.icon}
            as={NavLink}
            to={`${basePath}/${tab.path}`}
          >
            {tab.label}
          </Tab>
        ))}
      </TabList>

      <div className={styles.tabContent}>
        <Outlet />
      </div>
    </BasicPage>
  );
}
```

## Common Patterns

### Card with Hover Effect

```tsx
import { Card, CardHeader, Text } from '@fluentui/react-components';
import styles from './HoverCard.module.css';

export function HoverCard({ title, description, onClick }) {
  return (
    <Card className={styles.card} onClick={onClick}>
      <CardHeader
        header={<Text weight="semibold">{title}</Text>}
        description={<Text size={200}>{description}</Text>}
      />
    </Card>
  );
}
```

```css
.card {
  background: var(--semanticBackground2);
  border: 1px solid var(--semanticStrokeDivider);
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.card:hover {
  background: var(--semanticBackgroundHover);
}

.card:active {
  background: var(--semanticBackgroundPressed);
}
```

### Data Grid with Selection

```tsx
import {
  DataGrid,
  DataGridHeader,
  DataGridRow,
  DataGridHeaderCell,
  DataGridBody,
  DataGridCell,
  createTableColumn,
} from '@fluentui/react-components';

const columns = [
  createTableColumn({ columnId: 'name', renderHeaderCell: () => 'Name' }),
  createTableColumn({ columnId: 'status', renderHeaderCell: () => 'Status' }),
];

export function ItemGrid({ items }) {
  return (
    <DataGrid items={items} columns={columns} selectionMode="multiselect">
      <DataGridHeader>
        <DataGridRow>
          {({ renderHeaderCell }) => (
            <DataGridHeaderCell>{renderHeaderCell()}</DataGridHeaderCell>
          )}
        </DataGridRow>
      </DataGridHeader>
      <DataGridBody>
        {({ item }) => (
          <DataGridRow key={item.id}>
            {({ renderCell }) => <DataGridCell>{renderCell(item)}</DataGridCell>}
          </DataGridRow>
        )}
      </DataGridBody>
    </DataGrid>
  );
}
```

## Design Principles

1. **Extend, don't replace** - Wrap Fluent UI components to add custom behavior
2. **Use Fluent tokens first** - Fall back to custom CSS variables only when needed
3. **CSS Modules for custom styles** - Keep styles scoped and maintainable
4. **Accessibility by default** - Use semantic HTML and ARIA attributes
5. **Consistent spacing** - Use the spacing scale variables throughout

## References

- [Fluent UI React v9 Documentation](https://react.fluentui.dev/)
- [Fluent UI Tokens](https://react.fluentui.dev/?path=/docs/concepts-developer-tokens-colors--page)
- [design-tokens.md](./references/design-tokens.md) - Complete token reference
- [patterns.md](./references/patterns.md) - Page template implementations
- [components.md](./references/components.md) - Component wrapper catalog
