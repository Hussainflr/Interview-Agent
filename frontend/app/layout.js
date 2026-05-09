export const metadata = {
  title: 'AI Interview Agent',
  description: 'Real-time voice-based interview assistant',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}