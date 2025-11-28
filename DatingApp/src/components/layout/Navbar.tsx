import Link from 'next/link';
import styles from './Navbar.module.css';

export default function Navbar() {
    return (
        <nav className={styles.navbar}>
            <div className={`container ${styles.navContainer}`}>
                <Link href="/" className={styles.logo}>
                    Divine Connection
                </Link>

                <div className={styles.navLinks}>
                    <Link href="/about" className={styles.link}>소개</Link>
                    <Link href="/stories" className={styles.link}>성혼 간증</Link>
                    <Link href="/login" className={styles.link}>로그인</Link>
                    <Link href="/signup" className="btn btn-primary">회원가입</Link>
                </div>
            </div>
        </nav>
    );
}
