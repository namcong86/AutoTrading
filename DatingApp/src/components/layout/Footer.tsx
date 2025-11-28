import styles from './Footer.module.css';

export default function Footer() {
    return (
        <footer className={styles.footer}>
            <div className={`container ${styles.footerContainer}`}>
                <div className={styles.column}>
                    <h3 className={styles.logo}>Divine Connection</h3>
                    <p className={styles.tagline}>신앙 안에서 맺어지는 진지한 만남.</p>
                </div>

                <div className={styles.column}>
                    <h4>회사</h4>
                    <a href="#">서비스 소개</a>
                    <a href="#">채용</a>
                    <a href="#">문의하기</a>
                </div>

                <div className={styles.column}>
                    <h4>약관 및 정책</h4>
                    <a href="#">개인정보 처리방침</a>
                    <a href="#">이용약관</a>
                </div>
            </div>
            <div className={styles.copyright}>
                &copy; {new Date().getFullYear()} Divine Connection. All rights reserved.
            </div>
        </footer>
    );
}
