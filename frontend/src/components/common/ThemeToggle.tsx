import { Moon, Sun } from 'lucide-react'
import { motion } from 'framer-motion'
import { useThemeStore } from '../../stores/themeStore'

export default function ThemeToggle() {
  const { isDark, toggleTheme } = useThemeStore()

  return (
    <motion.button
      onClick={toggleTheme}
      className="p-2 rounded-lg bg-dark-card hover:bg-dark-border transition-colors"
      whileTap={{ scale: 0.95 }}
      title={isDark ? 'Light Mode' : 'Dark Mode'}
    >
      <motion.div
        initial={false}
        animate={{ rotate: isDark ? 0 : 180 }}
        transition={{ duration: 0.3 }}
      >
        {isDark ? (
          <Moon className="w-5 h-5 text-slate-400" />
        ) : (
          <Sun className="w-5 h-5 text-yellow-500" />
        )}
      </motion.div>
    </motion.button>
  )
}
