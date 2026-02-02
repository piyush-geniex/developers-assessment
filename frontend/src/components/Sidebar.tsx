'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

interface NavItem {
    href: string;
    label: string;
    icon: string;
}

const navItems: NavItem[] = [
    { href: '/', label: 'Dashboard', icon: '📊' },
    { href: '/worklogs', label: 'Worklogs', icon: '📋' },
    { href: '/payments', label: 'Process Payments', icon: '💳' },
    { href: '/payments/history', label: 'Payment History', icon: '📜' },
];

export default function Sidebar() {
    const pathname = usePathname();

    return (
        <aside className="sidebar">
            <div className="sidebar-logo">
                <span style={{ fontSize: '1.5rem' }}>💼</span>
                <h1>WorkLog</h1>
            </div>

            <nav>
                <ul className="nav-menu">
                    {navItems.map((item) => (
                        <li key={item.href}>
                            <Link
                                href={item.href}
                                className={`nav-item ${pathname === item.href ? 'active' : ''}`}
                            >
                                <span className="nav-icon">{item.icon}</span>
                                <span>{item.label}</span>
                            </Link>
                        </li>
                    ))}
                </ul>
            </nav>
        </aside>
    );
}
