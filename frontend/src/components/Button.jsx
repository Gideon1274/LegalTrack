export default function Button({ variant = 'primary', className = '', ...props }) {
    const base =
        'inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-slate-400 disabled:opacity-50 disabled:cursor-not-allowed'
    const styles =
        variant === 'primary'
            ? 'bg-slate-900 text-white hover:bg-slate-800'
            : 'bg-white text-slate-900 border border-slate-300 hover:bg-slate-50'

    return <button className={`${base} ${styles} ${className}`} {...props} />
}
