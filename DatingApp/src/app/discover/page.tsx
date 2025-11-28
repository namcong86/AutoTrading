'use client';

import { useState } from 'react';
import ProfileCard from '@/components/features/ProfileCard';
import Button from '@/components/ui/Button';
import styles from './page.module.css';

// Mock Data
const MOCK_PROFILES = [
    {
        id: 1,
        name: "지은",
        age: 26,
        location: "서울, 강남구",
        denomination: "장로교 (통합)",
        verse: "잠언 31:25",
        imageUrl: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?q=80&w=1887&auto=format&fit=crop",
        bio: "찬양팀에서 건반으로 섬기고 있습니다. 예쁜 카페 찾아다니는 걸 좋아해요. 하나님을 최우선으로 두는 분을 만나고 싶어요."
    },
    {
        id: 2,
        name: "다윗",
        age: 29,
        location: "부산, 해운대구",
        denomination: "감리교",
        verse: "시편 23:1",
        imageUrl: "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?q=80&w=1887&auto=format&fit=crop",
        bio: "청년부 교사로 섬기고 있습니다. 선교와 사진 찍는 것에 관심이 많아요. 믿음 안에서 함께 성장할 수 있는 분을 찾습니다."
    },
    {
        id: 3,
        name: "수민",
        age: 27,
        location: "경기도, 분당",
        denomination: "침례교",
        verse: "빌립보서 4:13",
        imageUrl: "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?q=80&w=1887&auto=format&fit=crop",
        bio: "매일 아침 큐티로 하루를 시작해요. 함께 성경 읽고 기도할 수 있는 믿음의 동역자를 만나고 싶습니다."
    }
];

export default function Discover() {
    const [currentIndex, setCurrentIndex] = useState(0);
    const [showMatch, setShowMatch] = useState(false);

    const currentProfile = MOCK_PROFILES[currentIndex];
    const isFinished = currentIndex >= MOCK_PROFILES.length;

    const handleLike = () => {
        // 50% 확률로 매칭 성공 시뮬레이션
        if (Math.random() > 0.5) {
            setShowMatch(true);
        } else {
            nextProfile();
        }
    };

    const handlePass = () => {
        nextProfile();
    };

    const nextProfile = () => {
        setCurrentIndex((prev) => prev + 1);
    };

    const closeMatch = () => {
        setShowMatch(false);
        nextProfile();
    };

    if (isFinished) {
        return (
            <div className={styles.container}>
                <div className={styles.emptyState}>
                    <h2>오늘의 소개가 끝났습니다!</h2>
                    <p>내일 새로운 인연이 도착할 거예요.</p>
                    <Button href="/messages" variant="outline">메시지 확인하기</Button>
                </div>
            </div>
        );
    }

    return (
        <div className={styles.container}>
            {showMatch && (
                <div className={styles.matchOverlay}>
                    <div className={styles.matchContent}>
                        <h1>It's a Match! 🎉</h1>
                        <p>{currentProfile.name}님과 연결되었습니다!</p>
                        <div className={styles.matchButtons}>
                            <Button href={`/messages/${currentProfile.id}`} variant="primary">메시지 보내기</Button>
                            <Button onClick={closeMatch} variant="outline" style={{ color: 'white', borderColor: 'white' }}>계속 탐색하기</Button>
                        </div>
                    </div>
                </div>
            )}

            <div className={styles.header}>
                <h1>새로운 인연 찾기</h1>
                <p>당신과 믿음의 여정을 함께할 사람을 찾아보세요.</p>
            </div>

            <div className={styles.cardContainer}>
                <ProfileCard
                    profile={currentProfile}
                    onLike={handleLike}
                    onPass={handlePass}
                />
            </div>

            <div className={styles.controls}>
                <p className={styles.hint}>오른쪽으로 스와이프하여 좋아요, 왼쪽은 패스</p>
            </div>
        </div>
    );
}
