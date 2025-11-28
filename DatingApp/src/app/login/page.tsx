import Link from 'next/link';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import styles from './page.module.css';

export default function Login() {
    return (
        <div className={styles.container}>
            <div className={styles.card}>
                <h1 className={styles.title}>환영합니다</h1>
                <p className={styles.subtitle}>로그인하여 여정을 계속하세요.</p>

                <form className={styles.form}>
                    <Input
                        label="이메일 주소"
                        type="email"
                        placeholder="john@example.com"
                    />
                    <Input
                        label="비밀번호"
                        type="password"
                        placeholder="••••••••"
                    />

                    <div className={styles.forgotPassword}>
                        <Link href="/forgot-password">비밀번호를 잊으셨나요?</Link>
                    </div>

                    <Button type="submit" className={styles.submitBtn}>로그인</Button>
                </form>

                <div className={styles.footer}>
                    계정이 없으신가요? <Link href="/signup">회원가입</Link>
                </div>
            </div>
        </div>
    );
}
