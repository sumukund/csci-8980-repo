import psycopg2
import psycopg2.extras
from typing import Dict, Any
import os

# PostgreSQL Schema
POSTGRES_SCHEMA = """
CREATE TABLE IF NOT EXISTS csci_8980_carbon_test (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    test_variant VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    duration_minutes NUMERIC(6,2),
    co2_grams NUMERIC(12,8) NOT NULL,
    co2_kg NUMERIC(12,10) NOT NULL,
    energy_kwh NUMERIC(12,10) NOT NULL,
    total_tokens INTEGER NOT NULL,
    total_requests INTEGER NOT NULL,
    miles_driven NUMERIC(12,8),
    gallons_gasoline NUMERIC(18,17),
    gallons_diesel NUMERIC(18,17),
    kwh_electricity NUMERIC(18,17),
    therms_natural_gas NUMERIC(18,17),
    led_bulb_hours NUMERIC(12,8),
    pounds_coal NUMERIC(18,17),
    barrels_oil NUMERIC(18,17),
    tree_seedlings_10_years NUMERIC(18,17),
    acres_forest_1_year NUMERIC(18,17),
    smartphone_charges NUMERIC(18,17),
    laptop_hours NUMERIC(12,8),
    netflix_hours NUMERIC(12,8),
    waste_recycling_tons NUMERIC(18,17),
    bottles_recycled NUMERIC(12,8),
    home_energy_days NUMERIC(18,17),
    water_heater_days NUMERIC(18,17),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def get_postgres_connection(database_url: str):
    """Get PostgreSQL connection"""
    conn = psycopg2.connect(database_url, cursor_factory=psycopg2.extras.RealDictCursor)
    return conn

def init_db(database_url: str = None):
    """Initialize database - PostgreSQL if URL provided"""
    if database_url:
        # Use PostgreSQL
        try:
            with get_postgres_connection(database_url) as conn:
                with conn.cursor() as cur:
                    cur.execute(POSTGRES_SCHEMA)
                conn.commit()
            print("PostgreSQL database initialized successfully")
        except Exception as e:
            print(f"Error initializing PostgreSQL database: {e}")
            raise

# Required fields for different tables

def insert_carbon_test_session(data: Dict[str, Any], database_url: str = None):
    """Insert carbon test session data - PostgreSQL if URL provided"""
    
    # Extract environmental impact data
    env_impact = data.get('environmental_impact', {})
    epa_equiv = data.get('epa_equivalencies', {})
    
    if database_url:
        # Use PostgreSQL
        try:
            with get_postgres_connection(database_url) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO csci_8980_carbon_test (
                            session_id, test_variant, timestamp, start_time, end_time, duration_minutes,
                            co2_grams, co2_kg, energy_kwh, total_tokens, total_requests,
                            miles_driven, gallons_gasoline, gallons_diesel, kwh_electricity, therms_natural_gas,
                            led_bulb_hours, pounds_coal, barrels_oil, tree_seedlings_10_years, acres_forest_1_year,
                            smartphone_charges, laptop_hours, netflix_hours, waste_recycling_tons, bottles_recycled,
                            home_energy_days, water_heater_days
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s
                        )""",
                        (
                            data.get('session_id'),
                            data.get('test_variant'),
                            data.get('timestamp'),
                            data.get('start_time'),
                            data.get('end_time'),
                            data.get('duration_minutes'),
                            env_impact.get('co2_grams', 0),
                            env_impact.get('co2_kg', 0),
                            env_impact.get('energy_kwh', 0),
                            env_impact.get('total_tokens', 0),
                            env_impact.get('total_requests', 0),
                            epa_equiv.get('miles_driven'),
                            epa_equiv.get('gallons_gasoline'),
                            epa_equiv.get('gallons_diesel'),
                            epa_equiv.get('kwh_electricity'),
                            epa_equiv.get('therms_natural_gas'),
                            epa_equiv.get('led_bulb_hours'),
                            epa_equiv.get('pounds_coal'),
                            epa_equiv.get('barrels_oil'),
                            epa_equiv.get('tree_seedlings_10_years'),
                            epa_equiv.get('acres_forest_1_year'),
                            epa_equiv.get('smartphone_charges'),
                            epa_equiv.get('laptop_hours'),
                            epa_equiv.get('netflix_hours'),
                            epa_equiv.get('waste_recycling_tons'),
                            epa_equiv.get('bottles_recycled'),
                            epa_equiv.get('home_energy_days'),
                            epa_equiv.get('water_heater_days')
                        )
                    )
                conn.commit()
        except Exception as e:
            print(f"Error inserting carbon test data into PostgreSQL: {e}")
            raise

def get_carbon_test_data(database_url: str = None, limit: int = None):
    """Retrieve carbon test session data from database"""
    query = "SELECT * FROM csci_8980_carbon_test ORDER BY created_at DESC"
    if limit:
        query += f" LIMIT {limit}"
    
    if database_url:
        # Use PostgreSQL
        try:
            with get_postgres_connection(database_url) as conn:
                with conn.cursor() as cur:
                    cur.execute(query)
                    return cur.fetchall()
        except Exception as e:
            print(f"Error retrieving data from PostgreSQL: {e}")
            raise

def get_carbon_test_summary(database_url: str = None):
    """Get summary statistics from carbon test data"""
    summary_query = """
    SELECT 
        test_variant,
        COUNT(*) as session_count,
        AVG(co2_grams) as avg_co2_grams,
        SUM(co2_grams) as total_co2_grams,
        AVG(energy_kwh) as avg_energy_kwh,
        SUM(energy_kwh) as total_energy_kwh,
        AVG(total_tokens) as avg_tokens,
        SUM(total_tokens) as total_tokens,
        AVG(duration_minutes) as avg_duration_minutes
    FROM csci_8980_carbon_test 
    GROUP BY test_variant
    ORDER BY test_variant
    """
    
    if database_url:
        try:
            with get_postgres_connection(database_url) as conn:
                with conn.cursor() as cur:
                    cur.execute(summary_query)
                    return cur.fetchall()
        except Exception as e:
            print(f"Error retrieving summary from PostgreSQL: {e}")
            raise
