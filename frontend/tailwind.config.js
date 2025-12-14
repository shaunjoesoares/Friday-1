/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                midnight: {
                    900: '#0f0c29',
                    800: '#302b63',
                    700: '#24243e',
                },
                neon: {
                    pink: '#ff00ff',
                    cyan: '#00ffff',
                    purple: '#bc13fe',
                    blue: '#00ccff'
                }
            },
            fontFamily: {
                sans: ['Inter', 'sans-serif'],
            },
        },
    },
    plugins: [],
}
