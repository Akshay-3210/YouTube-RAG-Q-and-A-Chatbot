import streamlit as st
from auth import google_login,generate_otp,verify_otp,save_otp,register_user,send_otp_email,login_user
from ytchatbot.app import render_youtube_chatbot

st.title("Youtube Video Q&A App")


if st.user.is_logged_in:
    user = google_login(st.user.name,st.user.email,st.user.sub)
    if user is None:
        st.error("Google user could not be saved.")
        st.stop()
    st.session_state["user"] = user

if "user" in st.session_state:
    user = st.session_state["user"]
    st.success("Login successful")
    st.write("Hello", user["name"])
    st.write(user["email"])

    if st.button("Logout"):
        st.session_state.clear()
        if st.user.is_logged_in:
            st.logout()
        # st.rerun()
    st.divider()
    render_youtube_chatbot()
        

else:
    register_tab, login_tab = st.tabs(["Register", "Login"])

    with register_tab:
        st.subheader("Create account") 
        name=st.text_input("Name")
        email=st.text_input("Email")
        password=st.text_input("Password",type="password")

        if st.button("Register"):
            if not name or not email or not password:
                st.error("Fill all details")
            elif len(password)<8:
                st.error("Password must be at least 8 characters long")
            else:
                user_id=register_user(name,email,password)
                if user_id:
                    otp=generate_otp()
                    save_otp(user_id,otp)
                    send_otp_email(email,otp)

                    st.session_state.user_id=user_id
                    st.session_state.otp_sent=True

                    st.success("OTP sent successfully")
                else:
                    st.error("Email may already be registered")
        if st.session_state.get("otp_sent",False):
            st.divider()

            st.subheader("Verify email")
            otp=st.text_input("enter OTP")

            if st.button("Verify OTP"):
                if verify_otp(st.session_state.user_id,otp):
                    st.success("Email verified successffully")

                    st.session_state.otp_sent=False
                    st.session_state.email_verified=True
                else:
                    st.error("Inavlid or expired OTP")

    with login_tab:
        st.subheader("Login")

        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password",type="password",key="login_password")
        if st.button("Login"):
            result = login_user(email, password)
            if result == "NOT_VERIFIED":
                st.warning("Please verify your email first.")
            elif result is None:
                st.error("Invalid email or password.")
            else:
                st.session_state.logged_in = True
                st.session_state.user = result
                st.rerun()
        if st.button("Login with Google"):
            st.login()
