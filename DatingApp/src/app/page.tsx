import Button from '@/components/ui/Button';
import styles from './page.module.css';

export default function Home() {
  return (
    <div className={styles.container}>
      {/* Hero Section */}
      <section className={styles.hero}>
        <div className={styles.heroContent}>
          <h1 className={styles.heroTitle}>
            하나님 안에서 <span className={styles.highlight}>거룩한 짝</span>을<br />만나보세요
          </h1>
          <p className={styles.heroSubtitle}>
            같은 믿음, 같은 가치관, 같은 비전을 가진 크리스천들과 연결되세요.<br />
            진지한 만남을 원하시는 분들을 위한 프리미엄 소개팅 서비스입니다.
          </p>
          <div className={styles.heroButtons}>
            <Button href="/signup" variant="primary">지금 시작하기</Button>
            <Button href="/about" variant="outline">더 알아보기</Button>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className={styles.features}>
        <div className="container">
          <h2 className={styles.sectionTitle}>왜 디바인 커넥션인가요?</h2>
          <div className={styles.featureGrid}>
            <div className={styles.featureCard}>
              <div className={styles.icon}>✝️</div>
              <h3>신앙 중심</h3>
              <p>교파, 교회 봉사, 좋아하는 성경 구절 등 신앙 생활을 중심으로 프로필을 작성합니다.</p>
            </div>
            <div className={styles.featureCard}>
              <div className={styles.icon}>🛡️</div>
              <h3>안전한 만남</h3>
              <p>철저한 본인 인증과 신앙 서약을 통해 검증된 회원들만 활동할 수 있습니다.</p>
            </div>
            <div className={styles.featureCard}>
              <div className={styles.icon}>💍</div>
              <h3>진지한 관계</h3>
              <p>가벼운 만남이 아닌, 결혼과 믿음의 가정을 꿈꾸는 분들을 위해 설계되었습니다.</p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className={styles.cta}>
        <div className={styles.ctaContent}>
          <h2>믿음의 동역자를 만날 준비가 되셨나요?</h2>
          <p>지금 바로 수많은 크리스천 청년들과 함께하세요.</p>
          <Button href="/signup" variant="primary" style={{ backgroundColor: '#fff', color: 'var(--primary-blue)' }}>
            무료로 가입하기
          </Button>
        </div>
      </section>
    </div>
  );
}
