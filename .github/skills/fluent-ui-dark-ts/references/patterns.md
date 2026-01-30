# Fluent UI Dark Theme Patterns

Page templates and layout patterns using **Fluent UI v9** components.

## Required Imports

```tsx
import { 
  FluentProvider,
  Button,
  TabList,
  Tab,
  DataGrid,
  DataGridHeader,
  DataGridRow,
  DataGridHeaderCell,
  DataGridBody,
  DataGridCell,
  createTableColumn,
} from '@fluentui/react-components';
import { 
  ArrowLeft24Regular,
  Settings24Regular,
  Add24Regular,
} from '@fluentui/react-icons';
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import clsx from 'clsx';
```

## App Layout

Root layout with FluentProvider and navigation:

```tsx
// components/AppLayout/AppLayout.tsx
import { FluentProvider } from '@fluentui/react-components';
import { darkTheme } from '../../theme/dark-theme';
import { Sidebar } from '../Sidebar/Sidebar';
import styles from './AppLayout.module.css';

interface AppLayoutProps {
  children: React.ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  return (
    <FluentProvider theme={darkTheme} className={styles.provider}>
      <div className={styles.layout}>
        <Sidebar />
        <main className={styles.main}>{children}</main>
      </div>
    </FluentProvider>
  );
}
```

```css
/* components/AppLayout/AppLayout.module.css */
.provider {
  min-height: 100vh;
  background: var(--colorNeutralBackground1);
}

.layout {
  display: flex;
  min-height: 100vh;
}

.main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}
```

## BasicPage - Standard Page Template

The foundational page template with header, back navigation, and content area:

```tsx
// components/BasicPage/BasicPage.tsx
import type { ReactNode } from 'react';
import { Button, Text } from '@fluentui/react-components';
import { ArrowLeft24Regular } from '@fluentui/react-icons';
import clsx from 'clsx';
import styles from './BasicPage.module.css';

export type ScrollMode = 'page' | 'content';

export interface BasicPageProps {
  /** Page title displayed in header */
  title?: string;
  /** Icon displayed before title */
  titleIcon?: ReactNode;
  /** Action buttons displayed in header */
  action?: ReactNode;
  /** Back button click handler */
  onGoBack?: () => void;
  /** URL to navigate to when back button clicked (alternative to onGoBack) */
  backButtonTarget?: string;
  /** Scroll behavior: 'page' scrolls entire page, 'content' scrolls only content area */
  scrollMode?: ScrollMode;
  /** Content rendered before header (e.g., banners) */
  preContent?: ReactNode;
  /** Banner component displayed at top of page */
  BannerComponent?: ReactNode;
  /** Additional CSS class */
  className?: string;
  /** Page content */
  children: ReactNode;
}

export function BasicPage({
  title,
  titleIcon,
  action,
  onGoBack,
  backButtonTarget,
  scrollMode = 'page',
  preContent,
  BannerComponent,
  className,
  children,
}: BasicPageProps) {
  const navigate = useNavigate();

  const handleGoBack = () => {
    if (onGoBack) {
      onGoBack();
    } else if (backButtonTarget) {
      navigate(backButtonTarget);
    }
  };

  const showBackButton = onGoBack || backButtonTarget;
  const showHeader = title || action || showBackButton;

  return (
    <div className={clsx(styles.page, styles[scrollMode], className)}>
      {BannerComponent}
      {preContent}

      {showHeader && (
        <header className={styles.header}>
          <div className={styles.titleRow}>
            {showBackButton && (
              <Button
                appearance="subtle"
                icon={<ArrowLeft24Regular />}
                onClick={handleGoBack}
                aria-label="Go back"
              />
            )}
            {titleIcon && <span className={styles.titleIcon}>{titleIcon}</span>}
            {title && (
              <Text as="h1" size={800} weight="semibold" className={styles.title}>
                {title}
              </Text>
            )}
          </div>
          {action && <div className={styles.actions}>{action}</div>}
        </header>
      )}

      <div className={styles.content}>{children}</div>
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

/* Page-level scrolling (default) */
.page.page {
  overflow-y: auto;
}

/* Content-level scrolling */
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

.titleIcon {
  display: flex;
  align-items: center;
  color: var(--colorNeutralForeground2);
}

.title {
  margin: 0;
  color: var(--colorNeutralForeground1);
}

.actions {
  display: flex;
  align-items: center;
  gap: var(--spacingS);
}

.content {
  flex: 1;
}
```

## ListPage - Data Grid Page

Page template optimized for displaying tabular data with DataGrid:

```tsx
// components/ListPage/ListPage.tsx
import type { ReactNode } from 'react';
import {
  DataGrid,
  DataGridHeader,
  DataGridRow,
  DataGridHeaderCell,
  DataGridBody,
  DataGridCell,
  Spinner,
  Text,
} from '@fluentui/react-components';
import type { TableColumnDefinition, DataGridProps } from '@fluentui/react-components';
import { BasicPage, type BasicPageProps } from '../BasicPage/BasicPage';
import styles from './ListPage.module.css';

export interface ListPageProps<T> extends Omit<BasicPageProps, 'children'> {
  /** Items to display in the grid */
  items: T[];
  /** Column definitions */
  columns: TableColumnDefinition<T>[];
  /** Unique key extractor for each item */
  getRowId: (item: T) => string;
  /** Loading state */
  isLoading?: boolean;
  /** Empty state message */
  emptyMessage?: string;
  /** Content rendered above the grid (filters, search) */
  toolbar?: ReactNode;
  /** Selection mode */
  selectionMode?: DataGridProps['selectionMode'];
  /** Row click handler */
  onRowClick?: (item: T) => void;
}

export function ListPage<T>({
  items,
  columns,
  getRowId,
  isLoading = false,
  emptyMessage = 'No items found',
  toolbar,
  selectionMode = 'none',
  onRowClick,
  ...pageProps
}: ListPageProps<T>) {
  if (isLoading) {
    return (
      <BasicPage {...pageProps}>
        <div className={styles.loadingState}>
          <Spinner size="large" />
        </div>
      </BasicPage>
    );
  }

  if (items.length === 0) {
    return (
      <BasicPage {...pageProps}>
        {toolbar}
        <div className={styles.emptyState}>
          <Text size={400} className={styles.emptyText}>
            {emptyMessage}
          </Text>
        </div>
      </BasicPage>
    );
  }

  return (
    <BasicPage {...pageProps} scrollMode="content">
      {toolbar && <div className={styles.toolbar}>{toolbar}</div>}

      <DataGrid
        items={items}
        columns={columns}
        getRowId={getRowId}
        selectionMode={selectionMode}
        className={styles.grid}
      >
        <DataGridHeader>
          <DataGridRow>
            {({ renderHeaderCell }) => (
              <DataGridHeaderCell>{renderHeaderCell()}</DataGridHeaderCell>
            )}
          </DataGridRow>
        </DataGridHeader>
        <DataGridBody<T>>
          {({ item, rowId }) => (
            <DataGridRow<T>
              key={rowId}
              onClick={onRowClick ? () => onRowClick(item) : undefined}
              className={onRowClick ? styles.clickableRow : undefined}
            >
              {({ renderCell }) => <DataGridCell>{renderCell(item)}</DataGridCell>}
            </DataGridRow>
          )}
        </DataGridBody>
      </DataGrid>
    </BasicPage>
  );
}
```

```css
/* components/ListPage/ListPage.module.css */
.toolbar {
  margin-bottom: var(--spacingL);
  flex-shrink: 0;
}

.grid {
  flex: 1;
  min-height: 0;
}

.clickableRow {
  cursor: pointer;
}

.clickableRow:hover {
  background: var(--semanticBackgroundHover);
}

.loadingState,
.emptyState {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
}

.emptyText {
  color: var(--colorNeutralForeground3);
}
```

### ListPage Usage Example

```tsx
import { createTableColumn, Button } from '@fluentui/react-components';
import { Add24Regular } from '@fluentui/react-icons';
import { ListPage } from '../components/ListPage/ListPage';

interface Project {
  id: string;
  name: string;
  status: string;
  updatedAt: string;
}

const columns = [
  createTableColumn<Project>({
    columnId: 'name',
    renderHeaderCell: () => 'Name',
    renderCell: (item) => item.name,
  }),
  createTableColumn<Project>({
    columnId: 'status',
    renderHeaderCell: () => 'Status',
    renderCell: (item) => <Badge>{item.status}</Badge>,
  }),
  createTableColumn<Project>({
    columnId: 'updatedAt',
    renderHeaderCell: () => 'Updated',
    renderCell: (item) => new Date(item.updatedAt).toLocaleDateString(),
  }),
];

function ProjectsPage() {
  const { data: projects, isLoading } = useProjects();
  const navigate = useNavigate();

  return (
    <ListPage
      title="Projects"
      action={
        <Button appearance="primary" icon={<Add24Regular />}>
          New Project
        </Button>
      }
      items={projects ?? []}
      columns={columns}
      getRowId={(item) => item.id}
      isLoading={isLoading}
      emptyMessage="No projects yet. Create your first project."
      onRowClick={(item) => navigate(`/projects/${item.id}`)}
    />
  );
}
```

## TabsPage - In-Page Tabs (No Routing)

Tabs within a page that switch content without URL changes:

```tsx
// components/TabsPage/TabsPage.tsx
import { useState, type ReactNode } from 'react';
import { TabList, Tab } from '@fluentui/react-components';
import type { SelectTabData } from '@fluentui/react-components';
import { BasicPage, type BasicPageProps } from '../BasicPage/BasicPage';
import styles from './TabsPage.module.css';

export interface TabDefinition {
  /** Unique tab identifier */
  id: string;
  /** Tab label text */
  label: string;
  /** Optional icon */
  icon?: ReactNode;
  /** Tab content (rendered when active) */
  content: ReactNode;
  /** Disable the tab */
  disabled?: boolean;
}

export interface TabsPageProps extends Omit<BasicPageProps, 'children'> {
  /** Tab definitions */
  tabs: TabDefinition[];
  /** Initially selected tab (defaults to first tab) */
  defaultTab?: string;
  /** Controlled selected tab */
  selectedTab?: string;
  /** Tab change handler */
  onTabChange?: (tabId: string) => void;
}

export function TabsPage({
  tabs,
  defaultTab,
  selectedTab: controlledSelectedTab,
  onTabChange,
  ...pageProps
}: TabsPageProps) {
  const [internalSelectedTab, setInternalSelectedTab] = useState(
    defaultTab ?? tabs[0]?.id
  );

  const selectedTab = controlledSelectedTab ?? internalSelectedTab;

  const handleTabSelect = (_: unknown, data: SelectTabData) => {
    const tabId = data.value as string;
    setInternalSelectedTab(tabId);
    onTabChange?.(tabId);
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
          <Tab
            key={tab.id}
            value={tab.id}
            icon={tab.icon}
            disabled={tab.disabled}
          >
            {tab.label}
          </Tab>
        ))}
      </TabList>

      <div className={styles.tabContent}>{activeTab?.content}</div>
    </BasicPage>
  );
}
```

```css
/* components/TabsPage/TabsPage.module.css */
.tabList {
  margin-bottom: var(--spacingXL);
  flex-shrink: 0;
}

.tabContent {
  flex: 1;
  min-height: 0;
}
```

### TabsPage Usage Example

```tsx
import { TabsPage } from '../components/TabsPage/TabsPage';
import { Settings24Regular, Person24Regular, Shield24Regular } from '@fluentui/react-icons';

function SettingsPage() {
  return (
    <TabsPage
      title="Settings"
      onGoBack={() => navigate(-1)}
      tabs={[
        {
          id: 'general',
          label: 'General',
          icon: <Settings24Regular />,
          content: <GeneralSettings />,
        },
        {
          id: 'profile',
          label: 'Profile',
          icon: <Person24Regular />,
          content: <ProfileSettings />,
        },
        {
          id: 'security',
          label: 'Security',
          icon: <Shield24Regular />,
          content: <SecuritySettings />,
        },
      ]}
    />
  );
}
```

## TabNavPage - Tabs with Routing

Tabs that map to routes with browser navigation support:

```tsx
// components/TabNavPage/TabNavPage.tsx
import type { ReactNode } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { TabList, Tab } from '@fluentui/react-components';
import { BasicPage, type BasicPageProps } from '../BasicPage/BasicPage';
import styles from './TabNavPage.module.css';

export interface TabNavDefinition {
  /** Unique tab identifier */
  id: string;
  /** Tab label text */
  label: string;
  /** Route path (relative to basePath) */
  path: string;
  /** Optional icon */
  icon?: ReactNode;
  /** Disable the tab */
  disabled?: boolean;
}

export interface TabNavPageProps extends Omit<BasicPageProps, 'children'> {
  /** Tab definitions with routing */
  tabs: TabNavDefinition[];
  /** Base path for tab routes */
  basePath: string;
}

export function TabNavPage({ tabs, basePath, ...pageProps }: TabNavPageProps) {
  const location = useLocation();

  // Determine selected tab from current URL
  const selectedTab = tabs.find((t) =>
    location.pathname === `${basePath}/${t.path}` ||
    location.pathname.startsWith(`${basePath}/${t.path}/`)
  )?.id ?? tabs[0]?.id;

  return (
    <BasicPage {...pageProps}>
      <TabList selectedValue={selectedTab} className={styles.tabList}>
        {tabs.map((tab) => (
          <Tab
            key={tab.id}
            value={tab.id}
            icon={tab.icon}
            disabled={tab.disabled}
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

```css
/* components/TabNavPage/TabNavPage.module.css */
.tabList {
  margin-bottom: var(--spacingXL);
  flex-shrink: 0;
}

.tabContent {
  flex: 1;
  min-height: 0;
}
```

### TabNavPage Route Configuration

```tsx
// routes.tsx
import { TabNavPage } from '../components/TabNavPage/TabNavPage';
import { Box24Regular, People24Regular, Settings24Regular } from '@fluentui/react-icons';

// Define tab navigation
const projectTabs = [
  { id: 'overview', label: 'Overview', path: 'overview', icon: <Box24Regular /> },
  { id: 'members', label: 'Members', path: 'members', icon: <People24Regular /> },
  { id: 'settings', label: 'Settings', path: 'settings', icon: <Settings24Regular /> },
];

// Route configuration
const routes = [
  {
    path: '/projects/:projectId',
    element: (
      <TabNavPage
        title="Project Name"
        onGoBack={() => navigate('/projects')}
        tabs={projectTabs}
        basePath="/projects/:projectId"
      />
    ),
    children: [
      { path: 'overview', element: <ProjectOverview /> },
      { path: 'members', element: <ProjectMembers /> },
      { path: 'settings', element: <ProjectSettings /> },
      { index: true, element: <Navigate to="overview" replace /> },
    ],
  },
];
```

## Common Layout Patterns

### Content with Sidebar

```tsx
function ContentWithSidebar({ sidebar, children }) {
  return (
    <div className={styles.splitLayout}>
      <aside className={styles.sidebar}>{sidebar}</aside>
      <section className={styles.mainContent}>{children}</section>
    </div>
  );
}
```

```css
.splitLayout {
  display: flex;
  gap: var(--spacingXL);
  height: 100%;
}

.sidebar {
  width: 280px;
  flex-shrink: 0;
}

.mainContent {
  flex: 1;
  min-width: 0;
}
```

### Card Grid Layout

```tsx
function CardGrid({ children, columns = 3 }) {
  return (
    <div 
      className={styles.cardGrid}
      style={{ '--columns': columns } as React.CSSProperties}
    >
      {children}
    </div>
  );
}
```

```css
.cardGrid {
  display: grid;
  grid-template-columns: repeat(var(--columns), 1fr);
  gap: var(--spacingL);
}

@media (max-width: 1200px) {
  .cardGrid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .cardGrid {
    grid-template-columns: 1fr;
  }
}
```

### Form Layout

```tsx
function FormSection({ title, description, children }) {
  return (
    <section className={styles.formSection}>
      <div className={styles.formHeader}>
        <Text size={500} weight="semibold">{title}</Text>
        {description && (
          <Text size={300} className={styles.description}>{description}</Text>
        )}
      </div>
      <div className={styles.formFields}>{children}</div>
    </section>
  );
}
```

```css
.formSection {
  display: flex;
  flex-direction: column;
  gap: var(--spacingL);
  padding-bottom: var(--spacingXXL);
  border-bottom: 1px solid var(--semanticStrokeDivider);
}

.formSection:last-child {
  border-bottom: none;
}

.formHeader {
  display: flex;
  flex-direction: column;
  gap: var(--spacingXS);
}

.description {
  color: var(--colorNeutralForeground3);
}

.formFields {
  display: flex;
  flex-direction: column;
  gap: var(--spacingL);
  max-width: var(--contentWidthM);
}
```

## Spacing Quick Reference

```
Page padding:          var(--spacingPagePadding) = 24px (16px mobile)
Header margin-bottom:  var(--spacingXL) = 20px
Card padding:          var(--spacingXL) = 20px
Card grid gap:         var(--spacingL) = 16px
Form field gap:        var(--spacingL) = 16px
Section gap:           var(--spacingXXL) = 24px
Tab list margin:       var(--spacingXL) = 20px
Button gap:            var(--spacingS) = 8px
Icon-text gap:         var(--spacingXS) = 4px
```
