# Fluent UI Dark Theme Design Tokens

Complete token reference for the Fluent UI v9-based dark theme system.

## Fluent UI Theme Tokens

These tokens are automatically available when using `FluentProvider` with a theme:

### Color Tokens

```typescript
// Access via theme object or CSS variables
// CSS: var(--colorBrandBackground)
// JS: theme.colorBrandBackground

// Brand colors (derived from BrandVariants)
colorBrandBackground          // Primary brand background
colorBrandBackgroundHover     // Brand hover state
colorBrandBackgroundPressed   // Brand pressed state
colorBrandForeground1         // Brand text on neutral background
colorBrandForeground2         // Secondary brand text
colorBrandStroke1             // Brand border color

// Neutral backgrounds (customized for dark theme)
colorNeutralBackground1       // hsl(240, 6%, 10%)  - Base page background
colorNeutralBackground2       // hsl(240, 5%, 12%)  - Elevated surfaces
colorNeutralBackground3       // hsl(240, 5%, 14%)  - Cards, panels
colorNeutralBackground4       // hsl(240, 4%, 18%)  - Dividers, subtle borders
colorNeutralBackground5       // hsl(240, 4%, 22%)  - Hover backgrounds
colorNeutralBackground6       // hsl(240, 4%, 26%)  - Active/pressed backgrounds

// Neutral foregrounds
colorNeutralForeground1       // Primary text (high contrast)
colorNeutralForeground2       // Secondary text
colorNeutralForeground3       // Tertiary/muted text
colorNeutralForeground4       // Disabled text
colorNeutralForegroundDisabled

// Neutral strokes (borders)
colorNeutralStroke1           // Default border
colorNeutralStroke2           // Subtle border
colorNeutralStroke3           // Very subtle border
colorNeutralStrokeAccessible  // High contrast border (accessibility)

// Status colors (palette tokens)
colorPaletteRedBackground1    // Error background (subtle)
colorPaletteRedBackground3    // Error background (strong)
colorPaletteRedForeground1    // Error text
colorPaletteGreenBackground1  // Success background (subtle)
colorPaletteGreenBackground3  // Success background (strong)
colorPaletteGreenForeground1  // Success text
colorPaletteYellowBackground1 // Warning background (subtle)
colorPaletteYellowForeground1 // Warning text
colorPaletteBlueBackground2   // Info background
colorPaletteBlueForeground2   // Info text
```

### Typography Tokens

```typescript
// Font families
fontFamilyBase                // 'Aptos', -apple-system, sans-serif
fontFamilyMonospace           // 'Cascadia Code', Consolas, monospace
fontFamilyNumeric             // For tabular data

// Font sizes
fontSizeBase100               // 10px
fontSizeBase200               // 12px
fontSizeBase300               // 14px (default body)
fontSizeBase400               // 16px
fontSizeBase500               // 20px
fontSizeBase600               // 24px
fontSizeHero700               // 28px
fontSizeHero800               // 32px
fontSizeHero900               // 40px
fontSizeHero1000              // 68px

// Font weights
fontWeightRegular             // 400
fontWeightMedium              // 500
fontWeightSemibold            // 600
fontWeightBold                // 700

// Line heights
lineHeightBase100             // 14px
lineHeightBase200             // 16px
lineHeightBase300             // 20px
lineHeightBase400             // 22px
lineHeightBase500             // 28px
lineHeightBase600             // 32px
lineHeightHero700             // 36px
lineHeightHero800             // 40px
lineHeightHero900             // 52px
lineHeightHero1000            // 92px
```

### Spacing Tokens

```typescript
// Fluent UI native spacing
spacingHorizontalNone         // 0
spacingHorizontalXXS          // 2px
spacingHorizontalXS           // 4px
spacingHorizontalSNudge       // 6px
spacingHorizontalS            // 8px
spacingHorizontalMNudge       // 10px
spacingHorizontalM            // 12px
spacingHorizontalL            // 16px
spacingHorizontalXL           // 20px
spacingHorizontalXXL          // 24px
spacingHorizontalXXXL         // 32px

// Same scale for vertical
spacingVerticalNone           // 0
spacingVerticalXXS            // 2px
spacingVerticalXS             // 4px
// ... etc
```

### Border Radius Tokens

```typescript
borderRadiusNone              // 0
borderRadiusSmall             // 2px
borderRadiusMedium            // 4px
borderRadiusLarge             // 6px
borderRadiusXLarge            // 8px
borderRadiusCircular          // 10000px
```

### Shadow Tokens

```typescript
shadow2                       // Subtle elevation
shadow4                       // Cards, dropdowns
shadow8                       // Dialogs, popovers
shadow16                      // Modals
shadow28                      // Floating elements
shadow64                      // Maximum elevation
```

## Custom CSS Variables

Additional tokens defined in `tokens.css` inside `.fui-FluentProvider`:

```css
.fui-FluentProvider {
  /* ===== EXTENDED SPACING SCALE ===== */
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
  
  /* Page-level spacing (responsive) */
  --spacingPagePadding: var(--spacingXXL);  /* 24px, 16px on mobile */

  /* ===== EXTENDED BORDER RADIUS ===== */
  --borderRadiusXXLarge: 12px;
  --borderRadiusXXXLarge: 24px;

  /* ===== CONTENT WIDTH CONSTRAINTS ===== */
  --contentWidthXS: 320px;
  --contentWidthS: 480px;
  --contentWidthM: 640px;
  --contentWidthL: 960px;
  --contentWidthXL: 1280px;

  /* ===== SEMANTIC BACKGROUND ALIASES ===== */
  /* Map to Fluent tokens for consistent naming */
  --semanticBackground1: var(--colorNeutralBackground1);
  --semanticBackground2: var(--colorNeutralBackground2);
  --semanticBackground3: var(--colorNeutralBackground3);
  --semanticBackground4: var(--colorNeutralBackground4);
  --semanticBackground5: var(--colorNeutralBackground5);
  --semanticBackground6: var(--colorNeutralBackground6);

  /* ===== SEMANTIC STROKE ALIASES ===== */
  --semanticStrokeDivider: var(--semanticBackground4);
  --semanticStrokeSubtle: var(--colorNeutralStroke2);
  --semanticStrokeDefault: var(--colorNeutralStroke1);

  /* ===== INTERACTIVE STATE COLORS ===== */
  /* Semi-transparent overlays for hover/press/select */
  --semanticBackgroundHover: hsl(0deg 0% 50% / 10%);
  --semanticBackgroundPressed: hsl(0deg 0% 0% / 40%);
  --semanticBackgroundSelected: hsl(0deg 0% 50% / 15%);

  /* ===== DATA VISUALIZATION COLORS ===== */
  --dataViz1: #8251EE;  /* Primary purple */
  --dataViz2: #3B82F6;  /* Blue */
  --dataViz3: #10B981;  /* Green */
  --dataViz4: #F59E0B;  /* Amber */
  --dataViz5: #EF4444;  /* Red */
  --dataViz6: #EC4899;  /* Pink */
  --dataViz7: #06B6D4;  /* Cyan */
}

/* Mobile adjustments */
@media (max-width: 640px) {
  .fui-FluentProvider {
    --spacingPagePadding: var(--spacingL);  /* 16px on mobile */
  }
}
```

## Brand Variants Reference

The purple brand color scale used in the theme:

```typescript
const brandVariants: BrandVariants = {
  10: '#030206',   // Darkest
  20: '#1A1326',
  30: '#2B1D44',
  40: '#38255E',
  50: '#472E79',
  60: '#553695',
  70: '#643FB2',
  80: '#8251EE',   // ← Primary brand color
  90: '#8251EE',
  100: '#9263F1',
  110: '#A175F3',
  120: '#AF86F5',
  130: '#BC98F7',
  140: '#C9AAF9',
  150: '#D5BCFB',
  160: '#E1CEFC',  // Lightest
};
```

## Token Usage Reference

### Background Hierarchy

| Layer | Token | Use Case |
|-------|-------|----------|
| Page | `colorNeutralBackground1` | Main page background |
| Surface | `colorNeutralBackground2` | Sidebars, panels |
| Card | `colorNeutralBackground3` | Cards, elevated surfaces |
| Divider | `colorNeutralBackground4` | Borders, separators |
| Hover | `colorNeutralBackground5` | Interactive hover states |
| Active | `colorNeutralBackground6` | Pressed/active states |

### Text Hierarchy

| Purpose | Token | Contrast |
|---------|-------|----------|
| Primary | `colorNeutralForeground1` | Maximum (titles, body) |
| Secondary | `colorNeutralForeground2` | Medium (descriptions) |
| Tertiary | `colorNeutralForeground3` | Low (hints, metadata) |
| Disabled | `colorNeutralForeground4` | Minimal (disabled text) |

### Spacing Usage

| Element | Recommended Token |
|---------|-------------------|
| Page padding | `--spacingPagePadding` (24px/16px) |
| Card padding | `--spacingXL` (20px) |
| Section gap | `--spacingXXL` (24px) |
| Form field gap | `--spacingL` (16px) |
| Button padding | `--spacingS` / `--spacingM` (8px/12px) |
| Input padding | `--spacingMNudge` / `--spacingM` (10px/12px) |
| Icon-text gap | `--spacingXS` (4px) |

### Component Token Mapping

| Component | Background | Border | Text |
|-----------|------------|--------|------|
| Page | `Background1` | - | `Foreground1` |
| Card | `Background3` | `StrokeSubtle` or none | `Foreground1` |
| Modal | `Background3` | `Stroke1` | `Foreground1` |
| Input | `Background2` | `Stroke1` | `Foreground1` |
| Button (secondary) | transparent | `Stroke1` | `Foreground1` |
| Button (primary) | `BrandBackground` | - | `ForegroundOnBrand` |
| Dropdown | `Background2` | `Stroke1` | `Foreground1` |
| Table header | `Background2` | - | `Foreground2` |
| Table row hover | `BackgroundHover` | - | `Foreground1` |

## Using Tokens in Code

### In CSS Modules

```css
.card {
  background: var(--colorNeutralBackground3);
  border: 1px solid var(--semanticStrokeDivider);
  border-radius: var(--borderRadiusLarge);
  padding: var(--spacingXL);
}

.card:hover {
  background: var(--semanticBackgroundHover);
}
```

### In TypeScript with makeStyles

```typescript
import { makeStyles, tokens } from '@fluentui/react-components';

const useStyles = makeStyles({
  card: {
    backgroundColor: tokens.colorNeutralBackground3,
    borderRadius: tokens.borderRadiusLarge,
    padding: tokens.spacingHorizontalXL,
    ':hover': {
      backgroundColor: tokens.colorNeutralBackground5,
    },
  },
});
```

### Accessing Theme in Components

```typescript
import { useTheme } from '@fluentui/react-components';

function ChartComponent() {
  const theme = useTheme();
  
  return (
    <Chart 
      colors={[
        theme.dataViz1,
        theme.dataViz2,
        theme.dataViz3,
      ]}
    />
  );
}
```
