import streamlit as st
from Analytic_board.analysis import calculate_nps
from Analytic_board.gpt_handler import *
from Analytic_board.future_board import forecast_nps
from Analytic_board.utils import *

# Streamlit interface
st.title("AI-Powered Product Insights")

# File upload
file = st.file_uploader("Upload a CSV or Excel file", type=["csv", "xlsx"])

# User input field
user_input = st.text_input("Ask a question about product performance:")

# Process the file and user input
if file and user_input:
    # Load the data
    if file.name.endswith('.csv'):
        data = pd.read_csv(file)
    elif file.name.endswith('.xlsx'):
        data = pd.read_excel(file)

    # Get the intent from GPT
    # intent = get_intent_from_gpt(user_input)
    predicted_intent = predict_intents_with_time(user_input)
    print("4th step")
    print(f"\n {predicted_intent}")
    for i in predicted_intent:
        query = dict_category(i.keys)
        timeline = dict_values(i.values)
        if query == 'forecast':
            if timeline == 'present':
                calculate_nps()
            else:
                date_cl, review_cl = components_of_file(data)
                fututre_nps = forecast_nps(data,date_cl, review_cl)
                st.write(f"The future nps score can be: {fututre_nps}")

        # elif query == 'best_product':
        #     if timeline == 'present':
        #         get_best_product()
        #     else:
        #         forecast_best_product()

        # elif query == 'worst_product':
        #     if timeline == 'present':
        #         get_worst_product()
        #     else:
        #         forecast_worst_product()

        # elif query == 'graphical':
        #     if timeline == 'present':
        #         current_graphs()
        #     else:
        #         future_graphs()
        # elif query == 'general':
        #     if timeline == 'present':
        #         present_summary():
        #     else:
        #         future_summary():



    # Based on intent, process the query
    # if 'nps score' in intent.lower():
    #     category = user_input.split('for')[-1].strip()  # Extract category
    #     nps_score = calculate_nps(data, 'Category', 'Rating', category)
    #     st.write(f"The NPS score for {category} is: {nps_score:.2f}")

    # elif 'forecast' in intent.lower() and 'nps score' in intent.lower():
    #     category = user_input.split('for')[-1].strip()  # Extract category
    #     forecasted_nps = forecast_nps(data, 'Category', 'Rating', category, months=6)
    #     st.write(f"The forecasted NPS score for {category} in 6 months is: {forecasted_nps:.2f}")

    # elif 'best product' in intent.lower():
    #     category = user_input.split('in')[-1].strip()  # Extract category
    #     best_product = get_best_product(data, 'Category', 'Rating', category)
    #     st.write(f"The best product in {category} is: {best_product}")

    # elif 'worst product' in intent.lower():
    #     category = user_input.split('in')[-1].strip()  # Extract category
    #     worst_product = get_worst_product(data, 'Category', 'Rating', category)
    #     st.write(f"The worst product in {category} is: {worst_product}")

    # elif 'report' in user_input.lower():
    #     # Generate a full report
    #     full_report = generate_full_report(data)
    #     st.write(full_report)

    # elif 'future prediction' in user_input.lower():
    #     # Forecast future metrics
    #     category = user_input.split('for')[-1].strip()  # Extract category
    #     future_nps, graphs = generate_future_graphs(data, 'Category', 'Rating', category, months=6)
    #     st.write(f"Future NPS for {category}: {future_nps}")
    #     st.plotly_chart(graphs['nps_happy_graph'])
    #     st.plotly_chart(graphs['user_satisfaction_graph'])

    # else:
    #     st.write("Sorry, I couldn't understand your request. Can you please rephrase it?")
