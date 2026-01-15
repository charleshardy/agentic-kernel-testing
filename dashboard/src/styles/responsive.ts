// Responsive design utilities and breakpoints

export const breakpoints = {
  xs: 480,
  sm: 576,
  md: 768,
  lg: 992,
  xl: 1200,
  xxl: 1600
};

export const mediaQueries = {
  xs: `@media (max-width: ${breakpoints.xs}px)`,
  sm: `@media (max-width: ${breakpoints.sm}px)`,
  md: `@media (max-width: ${breakpoints.md}px)`,
  lg: `@media (max-width: ${breakpoints.lg}px)`,
  xl: `@media (max-width: ${breakpoints.xl}px)`,
  xxl: `@media (max-width: ${breakpoints.xxl}px)`,
  
  // Min-width queries
  minXs: `@media (min-width: ${breakpoints.xs + 1}px)`,
  minSm: `@media (min-width: ${breakpoints.sm + 1}px)`,
  minMd: `@media (min-width: ${breakpoints.md + 1}px)`,
  minLg: `@media (min-width: ${breakpoints.lg + 1}px)`,
  minXl: `@media (min-width: ${breakpoints.xl + 1}px)`,
  minXxl: `@media (min-width: ${breakpoints.xxl + 1}px)`,
  
  // Touch devices
  touch: '@media (hover: none) and (pointer: coarse)',
  mouse: '@media (hover: hover) and (pointer: fine)'
};

export const spacing = {
  mobile: {
    xs: 4,
    sm: 8,
    md: 12,
    lg: 16,
    xl: 20
  },
  tablet: {
    xs: 8,
    sm: 12,
    md: 16,
    lg: 24,
    xl: 32
  },
  desktop: {
    xs: 8,
    sm: 16,
    md: 24,
    lg: 32,
    xl: 48
  }
};

export const touchTargets = {
  minimum: 44, // iOS minimum touch target
  recommended: 48, // Material Design recommendation
  comfortable: 56 // Comfortable touch target
};

export const typography = {
  mobile: {
    h1: { fontSize: 24, lineHeight: 1.3 },
    h2: { fontSize: 20, lineHeight: 1.35 },
    h3: { fontSize: 18, lineHeight: 1.4 },
    h4: { fontSize: 16, lineHeight: 1.45 },
    body: { fontSize: 14, lineHeight: 1.5 },
    small: { fontSize: 12, lineHeight: 1.5 }
  },
  tablet: {
    h1: { fontSize: 28, lineHeight: 1.3 },
    h2: { fontSize: 24, lineHeight: 1.35 },
    h3: { fontSize: 20, lineHeight: 1.4 },
    h4: { fontSize: 18, lineHeight: 1.45 },
    body: { fontSize: 15, lineHeight: 1.5 },
    small: { fontSize: 13, lineHeight: 1.5 }
  },
  desktop: {
    h1: { fontSize: 32, lineHeight: 1.3 },
    h2: { fontSize: 28, lineHeight: 1.35 },
    h3: { fontSize: 24, lineHeight: 1.4 },
    h4: { fontSize: 20, lineHeight: 1.45 },
    body: { fontSize: 16, lineHeight: 1.5 },
    small: { fontSize: 14, lineHeight: 1.5 }
  }
};

// Responsive grid configurations
export const gridConfig = {
  mobile: {
    columns: 4,
    gutter: 16,
    margin: 16
  },
  tablet: {
    columns: 8,
    gutter: 24,
    margin: 24
  },
  desktop: {
    columns: 12,
    gutter: 24,
    margin: 32
  }
};

// Device detection utilities
export const getDeviceType = (): 'mobile' | 'tablet' | 'desktop' => {
  if (typeof window === 'undefined') return 'desktop';
  
  const width = window.innerWidth;
  if (width < breakpoints.md) return 'mobile';
  if (width < breakpoints.lg) return 'tablet';
  return 'desktop';
};

export const isTouchDevice = (): boolean => {
  if (typeof window === 'undefined') return false;
  return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
};

export const isPortrait = (): boolean => {
  if (typeof window === 'undefined') return false;
  return window.innerHeight > window.innerWidth;
};

// Responsive component props
export interface ResponsiveProps {
  mobile?: any;
  tablet?: any;
  desktop?: any;
}

export const getResponsiveValue = <T,>(
  props: ResponsiveProps,
  defaultValue: T
): T => {
  const deviceType = getDeviceType();
  
  if (deviceType === 'mobile' && props.mobile !== undefined) {
    return props.mobile;
  }
  if (deviceType === 'tablet' && props.tablet !== undefined) {
    return props.tablet;
  }
  if (deviceType === 'desktop' && props.desktop !== undefined) {
    return props.desktop;
  }
  
  return defaultValue;
};

// CSS helper for responsive styles
export const responsiveStyle = (
  mobile: string,
  tablet?: string,
  desktop?: string
): string => {
  let styles = mobile;
  
  if (tablet) {
    styles += `
      ${mediaQueries.minMd} {
        ${tablet}
      }
    `;
  }
  
  if (desktop) {
    styles += `
      ${mediaQueries.minLg} {
        ${desktop}
      }
    `;
  }
  
  return styles;
};

// Safe area insets for mobile devices (notches, etc.)
export const safeAreaInsets = {
  top: 'env(safe-area-inset-top, 0px)',
  right: 'env(safe-area-inset-right, 0px)',
  bottom: 'env(safe-area-inset-bottom, 0px)',
  left: 'env(safe-area-inset-left, 0px)'
};
