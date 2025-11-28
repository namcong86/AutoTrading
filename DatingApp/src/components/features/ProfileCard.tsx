import React from 'react';
import styles from './ProfileCard.module.css';

interface ProfileProps {
    id: number;
    name: string;
    age: number;
    location: string;
    denomination: string;
    verse: string;
    imageUrl: string;
    bio: string;
}

interface ProfileCardProps {
    profile: ProfileProps;
    onLike: () => void;
    onPass: () => void;
}

export default function ProfileCard({ profile, onLike, onPass }: ProfileCardProps) {
    return (
        <div className={styles.card}>
            <div
                className={styles.imageContainer}
                style={{ backgroundImage: `url(${profile.imageUrl})` }}
            >
                <div className={styles.overlay}>
                    <div className={styles.info}>
                        <h2 className={styles.name}>{profile.name}, {profile.age}</h2>
                        <p className={styles.location}>{profile.location}</p>
                        <div className={styles.badge}>{profile.denomination}</div>
                    </div>
                </div>
            </div>

            <div className={styles.content}>
                <div className={styles.verse}>
                    "{profile.verse}"
                </div>
                <p className={styles.bio}>{profile.bio}</p>

                <div className={styles.actions}>
                    <button onClick={onPass} className={`${styles.actionBtn} ${styles.pass}`}>✕</button>
                    <button onClick={onLike} className={`${styles.actionBtn} ${styles.like}`}>♥</button>
                </div>
            </div>
        </div>
    );
}
