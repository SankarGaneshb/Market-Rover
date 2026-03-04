import '@testing-library/jest-dom';

const originalError = console.error;
const originalWarn = console.warn;

beforeAll(() => {
    console.error = (...args) => {
        // Suppress React 18 act() warnings that occur when testing components with async effects
        if (typeof args[0] === 'string' && /Warning.*not wrapped in act/.test(args[0])) {
            return;
        }
        // Suppress ReactDOMTestUtils deprecation warnings from React Testing Library
        if (typeof args[0] === 'string' && /Warning: `ReactDOMTestUtils.act` is deprecated/.test(args[0])) {
            return;
        }
        originalError.call(console, ...args);
    };

    console.warn = (...args) => {
        // Suppress React Router v7 future flag warnings
        if (typeof args[0] === 'string' && /React Router Future Flag Warning/.test(args[0])) {
            return;
        }
        originalWarn.call(console, ...args);
    };
});

afterAll(() => {
    console.error = originalError;
    console.warn = originalWarn;
});
