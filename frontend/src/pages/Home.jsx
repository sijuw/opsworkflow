import Header from "../components/layout/Header";
import PageContainer from "../components/layout/PageContainer";
import EmailForm from "../components/EmailForm";

export default function Home() {
  return (
    <>
      <Header />

      <PageContainer>
        <EmailForm />
      </PageContainer>
    </>
  );
}