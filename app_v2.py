import streamlit as st
from options import *
from pypdf import PdfReader 
from calculations import * 

st.set_page_config(
    page_title="ISDE Regelhulp", 
    page_icon="🏠", 
    layout="centered", 
    initial_sidebar_state="auto", 
    menu_items={"Get help" : 'https://www.rvo.nl'}
)

class Measure:
    def __init__(self, name, options, icon_path, subsidy_file=None):
        self.name = name
        self.options = options
        self.icon_path = icon_path
        self.subsidy_file = subsidy_file

class SubsidyApp:
    def __init__(self):
        self.measures = [
            Measure("heatpump", HEATPUMP_OPTIONS, "heatpump_icon.png", "/path/to/heatpump_subsidy.pdf"),
            Measure("insulation", INSULATION_OPTIONS, "insulation_icon.png"),
            Measure('zonneboiler', None, 'solar_icon.png')
        ]
        self.selected_measure = None # next job: deze gebruiken ipv st session state! Hij lijkt deze alleen niet te onthouden... 
        self.selected_type = None
        self.subsidy_amount= 0

    def run(self):
        format_option = lambda option: option.text

        # Initialize measure in session state
        if 'measure' not in st.session_state:
            st.session_state.measure = None    

        # 1. Welcome page 
        if 'check_started' not in st.session_state:
            with st.form(key='start_check'):
                st.markdown("<h3 style='color: #00007E;'>Begeleiding bij ISDE subsidie aanvragen</h3>", unsafe_allow_html=True)
                st.image("Wendy.png", caption="Samen ISDE aanvragen", use_column_width=False)
                check_started = st.form_submit_button("Start ISDE check")
                if check_started:
                    st.session_state.check_started = True

        # 2. Check started 
        if 'check_started' in st.session_state and st.session_state.measure is None:
            st.markdown("<h3 style='color: #00007E;'>Kies voor welke maatregelen je subsidie aan wilt vragen</h3>", unsafe_allow_html=True)
            # Display clickable icons for each measure option
            for measure in self.measures:
                st.image(measure.icon_path, use_column_width=False)
                if st.button("", key=measure.name, help=measure.name):
                    st.session_state.measure = measure

        # 3. Heatpump selected 
        if st.session_state.measure is not None:
            if st.session_state.measure.name == 'heatpump':
                    st.markdown("<h3 style='color: #00007E;'>Selecteer type warmtepomp</h3>", unsafe_allow_html=True)
                    with st.form(key="choose_heatpump_type"):
                        measure_type = st.selectbox(
                            "Welke warmtepomp heb je aangeschaft", 
                            HEATPUMP_OPTIONS, 
                            format_func=format_option,
                            key = 'heatpump_selectbox'
                        )

                        measureTypeSelectionDone = st.form_submit_button("Check subsidie")
                    if measureTypeSelectionDone:
                        st.write("Je hebt gekozen voor de volgende maatregel:", measure_type.text)
                        st.session_state.measure_type = measure_type

        # 3. Insulation selected 
        if st.session_state.measure is not None:
            if st.session_state.measure.name == 'insulation':
                    st.markdown("<h3 style='color: #00007E;'>Selecteer type isolatie</h3>", unsafe_allow_html=True)
                    with st.form(key="choose_insulation_type"):
                        measure_type = st.selectbox(
                            "Welke isolatie heb je gedaan", 
                            INSULATION_OPTIONS, 
                            format_func=format_option,
                            key = 'insulation_selextbox'
                        )

                        measureTypeSelectionDone = st.form_submit_button("Verder")
                    if measureTypeSelectionDone:
                        st.write("Je hebt gekozen voor de volgende maatregel:", measure_type.text)
                        st.session_state.measure_type = measure_type

        # 4. Subsidy calculation
                # Ensure that necessary session states are initialized
        if 'glass_type_done' not in st.session_state:
            st.session_state.glass_type_done = False

        if 'submit_options' not in st.session_state:
            st.session_state.submit_options = False

        # Main application logic
        if 'measure_type' in st.session_state:

            if st.session_state.measure.name == 'heatpump':
                # Assuming `get_heatpump_subsidy_amount` is defined
                self.subsidy_amount = get_heatpump_subsidy_amount(st.session_state.measure_type)
            
            if st.session_state.measure.name == "insulation" and measure_type.value != 'window_insulation':
                with st.form(key="choose_insulated_m2"):
                    number = st.number_input("Hoe veel M2 heb je geïsoleerd?", key='number_input')
                    m2Done = st.form_submit_button("Verder")
                if m2Done:
                    self.subsidy_amount = get_insulation_subsidy_amount(st.session_state.measure_type, number)

            if st.session_state.measure.name == "insulation" and measure_type.value == 'window_insulation':
                with st.form(key="choose_type_window"):
                    measure_type = st.selectbox(
                        "Triple of HR?", 
                        GLASS_OPTIONS, 
                        format_func=format_option,
                        key='glass_type_selection'
                    )
                    glass_type_done = st.form_submit_button("Verder")
                if glass_type_done:
                    st.session_state.glass_type_done = True

            if st.session_state.glass_type_done:
                with st.form(key="options_form"):
                    st.text('Kies of je een of meerdere van de volgende maatregelen getroffen hebt')
                    option1 = st.checkbox("Isolerende panelen in kozijnen", key='panelen')
                    option2 = st.checkbox("Isolerende deuren", key='deuren')
                    option3 = st.checkbox("Geen van beiden", key='None')
                    submit_options = st.form_submit_button("Submit Options")
                if submit_options:
                    st.session_state.submit_options = True
                    if option3 and not option1 and not option2:
                        with st.form(key="choose_insulated_m2"):
                            m2 = st.number_input("Hoe veel M2 heb je geïsoleerd?", key='number_input')
                            date_string = '2022-12-31'
                            date = datetime.strptime(date_string, '%Y-%m-%d')
                            m2Done = st.form_submit_button("Verder")
                        if m2Done:
                            self.subsidy_amount = get_glass_subsidy_amount(m2, measure_type.value, 'glass', date)
                        else:
                            st.success('Je komt niet in aanmerking voor subsidie')
                # 5. Print the result
                if self.subsidy_amount:
                    st.success(f"Je kan €{self.subsidy_amount} subsidie krijgen voor deze maatregel!")
                if self.subsidy_amount is None:
                    st.success(f"Je voldoet niet aan het minimum oppervlakte om voor subsidie in aanmerking te komen")

                # 6. Add another measure? Combinatie is x2 

if __name__ == '__main__':
    app=SubsidyApp()
    app.run()



