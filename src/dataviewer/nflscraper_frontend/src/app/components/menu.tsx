"use client";
import { usePathname } from "next/navigation";
import Link from "next/link";
import "@/app/globals.css";

export default function Menu() {
    const pathname = usePathname();

    const isActive = (route: string) => {
        return pathname === route ? 'tab-active' : '';
    }

    return (
        <div role="tablist" className="flex py-2 place-content-around ptabs tabs-boxed">
            <Link href="/" passHref>
                <div role="tab" className={`tab ${isActive('/')}`}>Home</div>
            </Link>
            <Link href="/view" passHref>
                <div role="tab" className={`tab ${isActive('/view')}`}>View</div>
            </Link>
            <Link href="/export" passHref>
                <div role="tab" className={`tab ${isActive('/export')}`}>Export</div>
            </Link>
        </div>
    );
}