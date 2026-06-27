module.exports = {
darkMode: "class",
content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
],
theme: {
    extend: {
    colors: {
        obsidian: "#0b0b0b",
        neonGreen: "#00ff7f",
        glitchRed: "#ff0044",
    },
    fontFamily: {
        greekRune: ["'Cinzel Decorative'", "serif"],
    },
    keyframes: {
        snakeWiggle: {
        "0%, 100%": { transform: "rotate(0deg)" },
        "25%": { transform: "rotate(3deg)" },
        "75%": { transform: "rotate(-3deg)" },
        },
    },
    animation: {
        snake: "snakeWiggle 2s infinite ease-in-out",
    },
    },
},
plugins: [],
};
