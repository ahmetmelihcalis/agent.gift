/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        paper: "#F9F9F6",
        ink: "#1C1917",
        navy: "#22304A",
        olive: "#677255",
      },
      fontFamily: {
        serif: ["var(--font-ui)", "system-ui", "sans-serif"],
        sans: ["var(--font-ui)", "system-ui", "sans-serif"],
      },
      boxShadow: {
        editorial: "0 24px 60px rgba(34, 48, 74, 0.08)",
      },
      keyframes: {
        rise: {
          "0%": { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" }
        }
      },
      animation: {
        rise: "rise 500ms ease-out forwards",
      }
    },
  },
  plugins: [],
};
