import Link from 'next/link';
import styles from './page.module.css';

const MOCK_CHATS = [
    {
        id: 1,
        name: "지은",
        lastMessage: "저도 그 말씀을 제일 좋아해요! 🙏",
        time: "2분 전",
        unread: 2,
        imageUrl: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?q=80&w=1887&auto=format&fit=crop"
    },
    {
        id: 2,
        name: "은혜",
        lastMessage: "이번 주일 예배 때 뵐까요?",
        time: "1시간 전",
        unread: 0,
        imageUrl: "https://images.unsplash.com/photo-1544005313-94ddf0286df2?q=80&w=1888&auto=format&fit=crop"
    }
];

export default function Messages() {
    return (
        <div className={styles.container}>
            <h1 className={styles.title}>메시지</h1>

            <div className={styles.chatList}>
                {MOCK_CHATS.map((chat) => (
                    <Link href={`/messages/${chat.id}`} key={chat.id} className={styles.chatItem}>
                        <div
                            className={styles.avatar}
                            style={{ backgroundImage: `url(${chat.imageUrl})` }}
                        />

                        <div className={styles.content}>
                            <div className={styles.header}>
                                <span className={styles.name}>{chat.name}</span>
                                <span className={styles.time}>{chat.time}</span>
                            </div>
                            <p className={`${styles.message} ${chat.unread > 0 ? styles.unread : ''}`}>
                                {chat.lastMessage}
                            </p>
                        </div>

                        {chat.unread > 0 && (
                            <div className={styles.badge}>{chat.unread}</div>
                        )}
                    </Link>
                ))}
            </div>
        </div>
    );
}
