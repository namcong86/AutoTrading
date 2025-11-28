import Link from 'next/link';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import styles from './page.module.css';

export default function Signup() {
    return (
        <div className={styles.container}>
            <div className={styles.card}>
                <h1 className={styles.title}>디바인 커넥션 가입하기</h1>
                <p className={styles.subtitle}>하나님 중심의 만남을 시작해보세요.</p>

                <form className={styles.form}>
                    <div className={styles.row}>
                        <Input label="이름" placeholder="길동" />
                        <Input label="성" placeholder="홍" />
                    </div>

                    <Input
                        label="이메일 주소"
                        type="email"
                        placeholder="john@example.com"
                    />
                    <Input
                        label="비밀번호"
                        type="password"
                        placeholder="안전한 비밀번호를 입력하세요"
                    />

                    <Button type="submit" className={styles.submitBtn}>계정 생성하기</Button>
                </form>

                <div className={styles.footer}>
                    이미 계정이 있으신가요? <Link href="/login">로그인</Link>
                </div>
            </div>
        </div>
    );
}
