import EmailForm from "../components/EmailForm";
import "../styles/home.css";

function Home() {

    return (

        <div className="page">

            <div className="card">

                <h1>OpsFlow</h1>

                <p>Email Notification Portal</p>

                <EmailForm/>

            </div>

        </div>
    );

}

export default Home;