
import json
import requests
from flask import Flask, render_template, request, jsonify, session
from token_manager import get_token
import uuid
import random
import os
from datetime import datetime
from ecologits import EcoLogits
from db import insert_carbon_test_session, init_db
from dotenv import load_dotenv
load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_KEY')

# API base urls
llm_base_url = os.getenv('LLM_BASE_URL')
bearer_token = get_token()

# Store active trackers for each session
active_trackers = {}

# Data logging configuration
DATA_LOG_FILE = 'user_sessions_data.json'

# A/B/C Test Variants
TEST_VARIANTS = {
    'A': 'no_emissions',      # No emissions shown
    'B': 'emissions_only',    # Show emissions without context
    'C': 'emissions_context'  # Show emissions with environmental context
}


def save_session_data(session_data):
    """Save session data to JSON file"""
    try:
        insert_carbon_test_session(session_data, DATABASE_URL)
    except Exception as e:
        print(f"Error saving session data: {e}")

def log_session_end(session_id, test_variant, cumulative_impacts, start_time=None):
    """Log session data when session ends"""
    try:
        session_data = {
            'session_id': session_id,
            'test_variant': test_variant,
            'timestamp': datetime.now().isoformat(),
            'start_time': start_time,
            'end_time': datetime.now().isoformat(),
            'duration_minutes': None,  # Will calculate if start_time available
            'environmental_impact': {
                'co2_grams': cumulative_impacts.get('co2_grams', 0),
                'co2_kg': cumulative_impacts.get('co2_grams', 0) / 1000,
                'energy_kwh': cumulative_impacts.get('energy_kwh', 0),
                'total_tokens': cumulative_impacts.get('total_tokens', 0),
                'total_requests': cumulative_impacts.get('requests', 0)
            },
            'epa_equivalencies': calculate_epa_equivalencies(
                cumulative_impacts.get('co2_grams', 0),
                cumulative_impacts.get('energy_kwh', 0)
            ) if cumulative_impacts.get('co2_grams', 0) > 0 else {}
        }
        
        # Calculate session duration if start time is available
        if start_time:
            try:
                start_dt = datetime.fromisoformat(start_time)
                end_dt = datetime.now()
                duration = (end_dt - start_dt).total_seconds() / 60
                session_data['duration_minutes'] = round(duration, 2)
            except:
                pass
        
        save_session_data(session_data)
        return session_data
        
    except Exception as e:
        print(f"Error logging session end: {e}")
        return None

def assign_test_variant():
    """Randomly assign a test variant to the user with weighted distribution (A:30%, B:30%, C:40%)"""
    variants = ['A', 'B', 'C']
    weights = [30, 30, 40]  # A, B, C percentages
    variant = random.choices(variants, weights=weights, k=1)[0]
    print(variant)
    return variant

def calculate_epa_equivalencies(co2_grams, energy_kwh=0):
    """Calculate EPA greenhouse gas equivalencies for given CO2 emissions"""
    co2_kg = co2_grams / 1000
    co2_metric_tons = co2_kg / 1000
    
    # EPA's official conversion factors (2023 data)
    equivalencies = {
        # Transportation
        'miles_driven': co2_grams / 404,  # g CO2/mile for average passenger vehicle
        'gallons_gasoline': co2_grams / 8887,  # g CO2/gallon of gasoline
        'gallons_diesel': co2_grams / 10180,  # g CO2/gallon of diesel
        
        # Energy
        'kwh_electricity': co2_grams / 386,  # g CO2/kWh (US average grid)
        'therms_natural_gas': co2_grams / 5300,  # g CO2/therm of natural gas
        'led_bulb_hours': (energy_kwh / 0.009) if energy_kwh > 0 else 0,  # 9W LED bulb
        
        # Coal and fossil fuels
        'pounds_coal': (co2_grams / 1011500) * 2000,  # lbs (from short ton conversion)
        'barrels_oil': co2_grams / 431000,  # g CO2/barrel of oil consumed
        
        # Carbon sequestration
        'tree_seedlings_10_years': co2_kg / 22,  # kg CO2 sequestered per tree in 10 years
        'acres_forest_1_year': co2_metric_tons / 0.84,  # metric tons CO2/acre/year
        
        # Technology and daily life
        'smartphone_charges': co2_grams / 8.22,  # g CO2 per full smartphone charge
        'laptop_hours': co2_grams / 50,  # Estimated g CO2 per hour of laptop use
        'netflix_hours': co2_grams / 36,  # g CO2 per hour of Netflix streaming
        
        # Waste and recycling
        'waste_recycling_tons': co2_metric_tons / 3.3,  # Paper recycling offset
        'bottles_recycled': co2_grams / 25,  # g CO2 saved per recycled plastic bottle
        
        # Home energy
        'home_energy_days': (energy_kwh / 30.1) if energy_kwh > 0 else 0,  # Daily avg home kWh
        'water_heater_days': (energy_kwh / 12) if energy_kwh > 0 else 0,  # Water heater daily kWh
    }
    
    return equivalencies

def get_emissions_context(cumulative_impacts):
    """Generate contextual information about CO2 emissions using EPA conversion factors"""
    co2_grams = cumulative_impacts.get('co2_grams', 0)
    energy_kwh = cumulative_impacts.get('energy_kwh', 0)
    
    if co2_grams <= 0:
        return "No significant emissions detected for this session."
    
    equiv = calculate_epa_equivalencies(co2_grams, energy_kwh)
    
    contexts = []
    
    if equiv['miles_driven'] >= 0.001:
        contexts.append(f" This is equivalent to driving {equiv['miles_driven']:.3f} miles in an average car.")
    
    if equiv['gallons_gasoline'] >= 0.0001:
        contexts.append(f" This equals burning {equiv['gallons_gasoline']:.4f} gallons of gasoline.")
    
    if equiv['smartphone_charges'] >= 0.1:
        contexts.append(f" This equals about {equiv['smartphone_charges']:.1f} full smartphone charges.")
    
    if equiv['led_bulb_hours'] >= 0.1:
        contexts.append(f" This could power an LED bulb for {equiv['led_bulb_hours']:.1f} hours.")
    
    if equiv['tree_seedlings_10_years'] >= 0.001:
        contexts.append(f" You'd need {equiv['tree_seedlings_10_years']:.3f} tree seedlings grown for 10 years to offset this.")
    
    if equiv['netflix_hours'] >= 0.1:
        contexts.append(f"This is equivalent to {equiv['netflix_hours']:.1f} hours of Netflix streaming.")
    
    if equiv['bottles_recycled'] >= 1:
        contexts.append(f"This could be offset by recycling {equiv['bottles_recycled']:.0f} plastic bottles.")
    
    if equiv['home_energy_days'] >= 0.01:
        contexts.append(f" This represents {equiv['home_energy_days']:.2f} days of average home energy use.")
    
    # Return a random context, or create a simple one if none apply
    if contexts:
        return contexts
    else:
        return f"This represents {co2_grams:.4f} grams of CO2 equivalent emissions."

@app.route("/")
def index():
    session['test_variant'] = assign_test_variant()
    init_db(DATABASE_URL)
    return render_template('index.html', test_variant=session['test_variant'])

@app.route("/chat", methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Get or create session ID
        session_id = session.get('session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
            session['session_id'] = session_id
            session['session_start_time'] = datetime.now().isoformat()
            session['messages'] = [{
                "role": "system",
                "content": "You are a helpful assistant. Answer the user's questions to the best of your ability."
            }]
            # Assign test variant if not already assigned
            if 'test_variant' not in session:
                session['test_variant'] = assign_test_variant()
                
        # Get existing messages or initialize
        messages = session.get('messages', [])
        
        # Add user message
        messages.append({"role": "user", "content": user_message})
        
        # Prepare API request
        chat_headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json",
            "X-TGT-APPLICATION": "gxcaiugcfrontend",
            "x-api-key": "YOUR DEVELOPER PORTAL API KEY",
        }
        
        chat_data = {
            "model": "gpt-4o",
            "temperature": 1,
            "max_new_tokens": 4095,
            "top_p": 1,
            "frequency_penalty": 0.5,
            "presence_penalty": 0,
            "timeout": 120,
            "stream": False,
            "messages": messages
        }
        
        # Send request to API
        response = requests.post(
            f"{llm_base_url}/chat/completions",
            headers=chat_headers,
            json=chat_data,
        )
        response.raise_for_status()
        
        chat_response = response.json()
        
        # Extract assistant's reply
        assistant_reply = chat_response.get("choices", [{}])[0].get("message", {}).get("content", "No response")
        
        # Extract token usage if available
        usage = chat_response.get("usage", {})
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        
        # Estimate environmental impact
        impact = estimate_environmental_impact(
            model_name=chat_data.get("model", "gpt-4o"),
            input_tokens=input_tokens,
            output_tokens=output_tokens
        )
        
        # Log the environmental impact
        print(f"Environmental Impact - Energy: {impact['energy_kwh']:.6f} kWh, "
              f"CO2: {impact['co2_grams']:.4f} g, Tokens: {impact['total_tokens']}")
        
        # Store cumulative impacts in session
        if 'cumulative_impacts' not in session:
            session['cumulative_impacts'] = {
                'energy_kwh': 0,
                'co2_grams': 0,
                'total_tokens': 0,
                'requests': 0
            }
        
        session['cumulative_impacts']['energy_kwh'] += impact['energy_kwh']
        session['cumulative_impacts']['co2_grams'] += impact['co2_grams']
        session['cumulative_impacts']['total_tokens'] += impact['total_tokens']
        session['cumulative_impacts']['requests'] += 1
        
        # Add assistant reply to messages
        messages.append({"role": "assistant", "content": assistant_reply})
        session['messages'] = messages
        
        return jsonify({
            'response': assistant_reply,
            'session_id': session_id,
            'test_variant': session.get('test_variant', 'A')
        })
        
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'API request failed: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route("/end_session", methods=['POST'])
def end_session():
    try:
        session_id = session.get('session_id')
        test_variant = session.get('test_variant', 'A')
        cumulative_impacts = session.get('cumulative_impacts', {
            'energy_kwh': 0,
            'co2_grams': 0,
            'total_tokens': 0,
            'requests': 0
        })
        
        co2_grams = cumulative_impacts['co2_grams']
        energy_kwh = cumulative_impacts['energy_kwh']
        
        
        
        # Prepare response based on test variant
        response_data = {
            'message': 'Session ended',
            'test_variant': test_variant,
            'emissions': {
                'co2_kg': co2_grams / 1000,  # Convert to kg
                'co2_grams': co2_grams,
                'energy_kwh': energy_kwh,
                'total_tokens': cumulative_impacts['total_tokens'],
                'requests': cumulative_impacts['requests']
            }
        }
        
        # Add contextual information for variant C
        if test_variant == 'C' and co2_grams > 0:
            response_data['emissions']['context'] = get_emissions_context(cumulative_impacts)
        
        # Log session data to JSON file
        session_start_time = session.get('session_start_time')
        logged_data = log_session_end(session_id, test_variant, cumulative_impacts, session_start_time)
        
        # Log the test variant and emissions for analysis (console)
        print(f"Session {session_id}: Variant {test_variant}")
        print(f"  Energy consumption: {energy_kwh:.6f} kWh")
        print(f"  GHG emissions: {co2_grams:.4f} g CO2eq")
        print(f"  Total tokens: {cumulative_impacts['total_tokens']}")
        print(f"  Total requests: {cumulative_impacts['requests']}")
        if logged_data and logged_data.get('duration_minutes'):
            print(f"  Session duration: {logged_data['duration_minutes']} minutes")
        
        # Clear session but keep test variant for potential new session
        session_variant = session.get('test_variant')
        session.clear()
        session['test_variant'] = session_variant
        
        return jsonify(response_data)
            
    except Exception as e:
        return jsonify({'error': f'Error ending session: {str(e)}'}), 500

@app.route("/test_info")
def test_info():
    """Get current test variant information"""
    variant = session.get('test_variant', 'A')
    return jsonify({
        'test_variant': variant,
        'variant_description': TEST_VARIANTS.get(variant)
    })
 
# Initialize EcoLogits (if we can use it)
try:
    EcoLogits.init()
    print("EcoLogits initialized successfully")
except Exception as e:
    print(f"EcoLogits initialization failed: {e}")

# Manual environmental impact estimation for Target API
def estimate_environmental_impact(model_name, input_tokens, output_tokens):
    """
    Estimate environmental impact based on model usage
    These are rough estimates based on research data
    """
    # Base estimates per 1000 tokens for different models (in gCO2eq)
    model_emissions = {
        'gpt-4': 2.93,  # gCO2eq per 1000 tokens
        'gpt-4o': 1.47,  # Optimized version, roughly half
        'gpt-3.5-turbo': 0.65,
        'default': 1.47  # Use GPT-4o as default
    }
    
    # Get emissions factor for the model
    emissions_factor = model_emissions.get(model_name.lower(), model_emissions['default'])
    
    # Calculate total tokens and emissions
    total_tokens = (input_tokens or 0) + (output_tokens or 0)
    estimated_co2_grams = (total_tokens / 1000) * emissions_factor
    estimated_energy_kwh = estimated_co2_grams * 0.002  # Rough conversion
    
    return {
        'energy_kwh': estimated_energy_kwh,
        'co2_grams': estimated_co2_grams,
        'total_tokens': total_tokens,
        'input_tokens': input_tokens or 0,
        'output_tokens': output_tokens or 0
    }

if __name__ == "__main__":
    app.run(debug=True)
