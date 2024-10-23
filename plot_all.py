import os
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from scipy.optimize import curve_fit

# Specify the directory containing the CSV files
output_directory = 'data_chunks'  # Directory where the chunk CSV files are saved


# Define the sine model function with adjusted amplitude calculation
def sine_model(x, max_value, frequency, phase, vertical_shift):
    amplitude = max_value - vertical_shift  # Amplitude based on max_value and vertical shift
    return amplitude * np.sin(frequency * x + phase) + vertical_shift


# Create a single figure for all the plots
fig = go.Figure()

# Initialize a counter for the files
file_count = 0

# Define a color for each AC current column
color_map = {
    'nmac3': 'blue',  # Blue
    'nmac4': 'yellow',  # Orange
    'nmac5': 'green',  # Green
    'nmac6': 'red'  # Red
}

# Loop through each CSV file in the specified directory
for csv_file in os.listdir(output_directory):
    if csv_file.endswith('.csv'):
        csv_file_path = os.path.join(output_directory, csv_file)

        # Read the CSV file with semicolon as the delimiter
        data = pd.read_csv(csv_file_path, delimiter=';')

        # Check if required columns exist
        required_columns = {'row_num', 'nmac3', 'nmac4', 'nmac5', 'nmac6'}
        if not required_columns.issubset(data.columns):
            print(f"Skipping {csv_file}: missing required columns.")
            continue

        # Increment file count
        file_count += 1

        # Only plot every 40th file
        if file_count % 40 != 0:
            continue

        # Select rows
        base_point = 0  # Starting point, location of idx 0
        limited_data = data.iloc[base_point:base_point + 1024]  # Get rows

        # Extract the relevant columns
        x_data = limited_data['row_num']  # Independent variable

        # Loop through each AC current column: nmac3, nmac4, nmac5, and nmac6
        for col in ['nmac3', 'nmac4', 'nmac5', 'nmac6']:
            y_data = limited_data[col]  # Dependent variable for AC current

            # Smoothing (optional)
            window_size = 40  # You can adjust this
            smoothed_y_data = y_data.rolling(window=window_size, center=True, min_periods=1).mean()

            # Set max_value from the current chunk
            max_value = np.max(y_data)

            # Initial guesses for the parameters
            estimated_frequency = 2 * np.pi / (x_data.max() - x_data.min())  # Frequency estimate
            initial_guesses = [estimated_frequency, 0, np.median(smoothed_y_data)]  # Updated to include vertical shift

            # Perform curve fitting
            try:
                popt, pcov = curve_fit(
                    lambda x, frequency, phase, vertical_shift: sine_model(x, max_value, frequency, phase,
                                                                           vertical_shift),
                    x_data, smoothed_y_data, p0=initial_guesses)
                frequency, phase, vertical_shift = popt
                print(f"Fitted parameters for {csv_file} ({col}): Frequency: {frequency}, Phase: {phase}\n")
            except Exception as e:
                print(f"An error occurred during curve fitting for {csv_file} ({col}): {e}")
                continue  # Skip to the next file in case of error

            # Generate fitted values for plotting
            y_fit = sine_model(x_data, max_value, *popt)

            # Calculate the x shift based on the phase
            x_shift = phase / frequency  # This gives the shift in the x direction

            # Apply the x shift to x_data
            shifted_x_data = x_data + x_shift

            if frequency < 0.01:
                # Add traces for the AC Current and fitted sine wave to the single figure
                fig.add_trace(go.Scatter(
                    x=shifted_x_data, y=y_data, mode='lines', name=f'{col} - {csv_file}',
                    line=dict(width=2, color=color_map[col], dash='solid'), opacity=0.7))
                fig.add_trace(go.Scatter(
                    x=shifted_x_data, y=y_fit, mode='lines', name=f'Fitted Sine ({col}) - {csv_file}',
                    line=dict(width=1, color=color_map[col], dash='dash'), opacity=0.9))

# Update layout with title and axis labels
fig.update_layout(
    title='AC Current Fitting - Overlapped Graphs with X Shift',
    xaxis_title='Index (idx)',
    yaxis_title='AC Current Values',
    legend_title='Legend',
    showlegend=True,
)

# Show grid (optional in plotly; you can customize gridlines)
fig.update_xaxes(showgrid=True)
fig.update_yaxes(showgrid=True)

# Adjust layout (optional, but helps in some cases)
fig.update_layout(margin=dict(l=40, r=40, t=40, b=40))

# Show the combined plot
fig.show()
