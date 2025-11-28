import Link from 'next/link';
import Button from '@/components/ui/Button';
import styles from './page.module.css';

export default function ChatRoom({ params }: { params: { id: string } }) {
    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <Link href="/messages" className={styles.backBtn}>←</Link>
                <div className={styles.headerInfo}>
                    <div className={styles.avatar} />
                    <span className={styles.name}>지은</span>
                </div>
                <div className={styles.actions}>⋮</div>
            </div>

            <div className={styles.messageList}>
                <div className={`${styles.message} ${styles.received}`}>
                    안녕하세요! 프로필 보니까 등산 좋아하신다고 해서요. 🏔️
                    <span className={styles.time}>오전 10:30</span>
                </div>
                <div className={`${styles.message} ${styles.sent}`}>
                    네! 하나님이 만드신 자연을 보는 걸 좋아해요. 등산 자주 가시나요?
                    <span className={styles.time}>오전 10:32</span>
                </div>
                <div className={`${styles.message} ${styles.received}`}>
                    저도 그 말씀을 제일 좋아해요! 🙏
                    <span className={styles.time}>오전 10:35</span>
                </div>
            </div>

            <div className={styles.inputArea}>
                <input
                    type="text"
                    placeholder="메시지를 입력하세요..."
                    className={styles.input}
                />
                <Button className={styles.sendBtn}>전송</Button>
            </div>
        </div>
    );
}
