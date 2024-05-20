import streamlit as st
import os
from langchain_groq import ChatGroq
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from app import load_vectors
import random
from pymongo.mongo_client import MongoClient
import re
from captcha.image import ImageCaptcha

os.environ["GROQ_API_KEY"]= st.secrets["GROQ_API_KEY"]
os.environ["HF_API_KEY"]= st.secrets["HF_API_KEY"]
os.environ["LANGCHAIN_TRACING_V2"]= st.secrets["LANGCHAIN_TRACING_V2"]
os.environ["LANGCHAIN_ENDPOINT"]= st.secrets["LANGCHAIN_ENDPOINT"]
os.environ["LANGCHAIN_API_KEY"]= st.secrets["LANGCHAIN_API_KEY"]
os.environ["LANGCHAIN_PROJECT"]= st.secrets["LANGCHAIN_PROJECT"]

Client = MongoClient("mongodb+srv://rahulmanocha21:mongodb@geminiresponse.f6hhnhi.mongodb.net/?retryWrites=true&w=majority&appName=GeminiResponse")
mydatabase = Client.ITDatabase
table = mydatabase.GeminiResponseTable


def validate_email(email):
    # Regular expression for a basic email validation
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    
    # Check if the entered email matches the pattern
    if re.match(email_pattern, email):
        return True
    else:
        return False
    
def generate_captcha():
    char_set = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    text_length = 6  # Adjust text length as needed
    captcha_text = ''.join(random.sample(char_set, text_length))
    
    if 'captcha' not in st.session_state or st.session_state['captcha']==False:
        st.session_state['captcha'] = captcha_text
    image = ImageCaptcha(width=400, height=100)
    image_data = image.generate(st.session_state['captcha'])
    image_bytes = image_data.getbuffer().tobytes()
    st.image(image=image_bytes)
    # print(st.session_state['captcha'])
    user_entered_captcha = st.text_input("Enter Captcha",max_chars=6)
    if st.session_state['captcha'].lower().strip() == user_entered_captcha.lower().strip():
            st.success('Captcha clear successfully and your response is on its way.')
            st.session_state['captcha']=False
            del st.session_state['captcha']
            return True
    else:
         st.error('Please enter Valid Captcha Code')


llm = ChatGroq(groq_api_key=os.environ['GROQ_API_KEY'], model_name="llama3-8b-8192")


try:
    st.markdown("""<h1 style="color:#ffffff; text-align:center  "> GardensAlive AI☘️</h1> """, unsafe_allow_html=True)
    st.markdown("""<h6 style="color:#039F20; text-align:center "> Your garden is practically begging for a makeover, and guess who's holding the magic wand?<br> Yup, it's you! Share a few secrets, and let's conjure up a garden masterpiece.</h6> """, unsafe_allow_html=True)
    New = st.toggle('Want to Generate New Plan')
    Email = st.text_input('Email Address')
    if New:
         with st.form("form", border=True):
            left ,middle, right =st.columns(3)
            Location = left.selectbox('Location', ["United States"])
            zone = left.selectbox('Hardiness Zone', ["Zone 1a", "Zone 1b", "Zone 2a", "Zone 2b", "Zone 3a", "Zone 3b", "Zone 4a", "Zone 4b", "Zone 5a", "Zone 5b", "Zone 6a", "Zone 6b", "Zone 7a", "Zone 7b", "Zone 8a", "Zone 8b", "Zone 9a", "Zone 9b", "Zone 10a", "Zone 10b", "Zone 11a", "Zone 11b", "Zone 12a", "Zone 12b", "Zone 13a", "Zone 13b"])
            soiltype = left.selectbox('Soil Type', ['🌱 Clay', '🪨 Silty', '⛱️ Sandy', '🌿 Loam'])
            Gardening_Experience  = left.selectbox('How much experience do you have with gardening?',['Beginner', 'Intermediate','Advanced'])
            PlantPrefrence = middle.multiselect("Select Plants:", ["🌸 Flowers","🌿 Herbs","🥦 Vegetables","🍓 Fruits","🌳 Trees","🌴 Shrubs","🌾 Grasses","🌵 Succulents","🌵 Cacti","🌿 Ferns","🌱 Mosses","🌿 Vines","💧 Aquatics","🌷 Bulbs","🌺 Orchids"])   
            Style  = middle.selectbox("🌿 Gardening Style", ('Organic', 'Conventional'))
            Budget  = middle.selectbox("Gardening Budget 💰", ('Low', 'Medium', 'High'))
            Time  = middle.selectbox("Gardening Time ⏰", ('Low', 'Medium', 'High'))
            Maintenance = right.selectbox("Maintenance Preference 🛠️", ('Low', 'Medium', 'High'))
            Allergies = right.multiselect('Any Kind of Allergies?', ("Pollen", "Bees", "Insects", "Mold", "Dust", "Grass", "Trees", "Shrubs", "Flowers", "Weeds"))
            LengthSpace =  right.number_input("Enter length of your garden (In Feet)", step=5)
            BreadthSpace =  right.number_input("Enter breadth of your garden (In Feet)",step=5)
            with middle:
                status = generate_captcha()
            if st.form_submit_button("Get Your Customized Gardening Plan",use_container_width=True):
                        if validate_email(Email):
                            pass
                        else:
                            st.error('Enter a Valid Email ID!')
                        if LengthSpace != 0.00 and BreadthSpace !=0.00 and status:
                            input_text = f'''You are a botanical expert, 
                                I am from {Location} and my zone is {zone}, Here type of soil is {soiltype}, I am at {Gardening_Experience} level in gardening, I want to have {PlantPrefrence} in my garden.
                                I want to do in {Style} style gardening.  My budget is {Budget}, time is {Time} and Maintenance preference is {Maintenance}. 
                                I am allergic from {Allergies}. I have {LengthSpace} X {BreadthSpace} feet space for my gardening region.
                                Provide me a detailed Gardening Plan with the plant names and there refrence links from context.
                                '''
                                
                            prompt = ChatPromptTemplate.from_template(
                                """
                                You are an AI assistant name 'GardensAlive AI Bot'. 
                                Answer the questions based on the provided context only if there is something out of context, response as 'Hi there, Ask me about the Gardening products and services only'. 
                                Please do not use explictly in your response that it is based on context.
                                Please response in well structure manner for example: 
                                Details Summary
                                Step by Step Detailed Planner according to the Inputs
                                1. Soil Preparation
                                2. Plant Selection
                                3. Planting
                                4. Watering and Mulching
                                5. Fertilizing
                                6. Maintenance
                                7. Winter Protection (if applicable)

                                Provide Best 5 Relevant to question matched URL Resources from context and brecks brand only.

                                <context>
                                {context}
                                <context>
                                Questions:{input}
                                """
                            )
                            vectors = load_vectors()
                            document_chain = create_stuff_documents_chain(llm, prompt)
                            retriever = vectors.as_retriever()
                            retrieval_chain = create_retrieval_chain(retriever, document_chain)
                            response = retrieval_chain.invoke({"input": input_text})
                            st.subheader("Your Customized Plan: ")
                            st.write(response['answer'])
                            document = {"email": Email.lower(), "response": response['answer']}
                            result = table.update_one({"email": Email}, {"$set": {"response": response['answer']}}, upsert=True)
                            st.write(f"You can also check your plan again using your email: {Email}.")
                        
                        else:
                            st.warning("Please recheck details you entered.")
    else:
        GetLast = st.button('GetLastResponse')
        if GetLast:
            if validate_email(Email):
                pass
            else:
                st.error("Invalid Email ID! Please enter Valid Email Id.")
            count = table.count_documents({"email": Email.lower()})
            if count!=0:
                    responses = table.find({"email": Email.lower()})
                    st.write_stream(i['response'] for i in responses)
            else:
                st.error(f'There is no plan found that is already generated for this Email : {Email}')
            
except Exception as e:
     st.error(f"Error occured {e}")
     st.info('AI is down due to high requests. Get Back to us after a moment.')

     
      
