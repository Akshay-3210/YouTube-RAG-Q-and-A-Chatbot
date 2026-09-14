from pathlib import Path
from urllib.parse import parse_qs, urlparse
import os
import chromadb
import streamlit as st
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_classic.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda, RunnableParallel, RunnablePassthrough
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint, HuggingFaceEndpointEmbeddings
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled
from youtube_transcript_api._errors import IpBlocked, NoTranscriptFound


def format_docs(retrieved_docs):
    return "\n\n".join(doc.page_content for doc in retrieved_docs)


def render_youtube_chatbot():
    load_dotenv(Path(__file__).with_name(".env"))

    embedding = HuggingFaceEndpointEmbeddings(
        model="sentence-transformers/all-MiniLM-L6-v2"
    )
    llm = HuggingFaceEndpoint(
        repo_id="Qwen/Qwen3.8-27B:ovhcloud",
        task="text-generation",
        temperature=0,
    )
    model = ChatHuggingFace(llm=llm)

    cloud_client = chromadb.CloudClient(
        api_key=os.getenv("CHROMA_API_KEY"),
        tenant=os.getenv("CHROMA_TENANT"),
        database=os.getenv("CHROMA_DATABASE"),
    )
    vector_store = Chroma(
        client=cloud_client,
        embedding_function=embedding,
        collection_name="sample",
    )


    url = st.text_input("enter youtube video url")

    if st.button("Load Video") and url:
        video_id = parse_qs(urlparse(url).query).get("v", [None])[0]

        if not video_id:
            st.error("Please enter a valid YouTube video URL")
            return

        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        existing = vector_store.get(where={"video_id": video_id})

        if existing["ids"]:
            st.info("Video already exists in database. Skipping saving...")
        else:
            try:
                transcript_list = YouTubeTranscriptApi().fetch(video_id, languages=["en"])
                transcript = " ".join(chunk.text for chunk in transcript_list)
            except (TranscriptsDisabled, NoTranscriptFound):
                st.error("No transcript available")
                return
            except IpBlocked:
                st.error("Youtube is temporarily blocking transcript requests from this IP.")
                return

            chunks = splitter.create_documents(
                [transcript], metadatas=[{"video_id": video_id, "source": url}]
            )
            ids = [f"{video_id}_{i}" for i in range(len(chunks))]
            vector_store.add_documents(chunks, ids=ids)
            st.success("Video added successfully in vector db")

        st.session_state["video_id"] = video_id
        st.session_state["video_loaded"] = True

    if st.session_state.get("video_loaded", False):
        retriever = vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 4, "filter": {"video_id": st.session_state["video_id"]}},
        )

        prompt = PromptTemplate(
            template="""
            You are a helpful assistant.
            Answer ONLY from the provided transcript context.
            If the context is insufficient, just say you don't know.

            {context}
            Question: {question}
            """,
            input_variables=["context", "question"],
        )

        parallel_chain = RunnableParallel({
            "context": retriever | RunnableLambda(format_docs),
            "question": RunnablePassthrough(),
        })

        main_chain = parallel_chain | prompt | model | StrOutputParser()
        question = st.text_input("enter query about the video content")

        if st.button("submit"):
            if not question.strip():
                st.warning("Please enter a question.")
            else:
                answer = main_chain.invoke(question)
                st.write(answer)
