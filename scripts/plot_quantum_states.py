import plotly.graph_objects as go
import numpy as np

# Generate some example data
time = np.linspace(0, 10, 100)
amplitude = np.sin(time)

# Create an interactive plot with Plotly
fig = go.Figure()
fig.add_trace(go.Scatter(x=time, y=amplitude, mode='lines', name='Quantum State Amplitude'))
fig.update_layout(title='Quantum State Visualization', xaxis_title='Time', yaxis_title='Amplitude')

# Save the plot as an HTML file
output_html = 'tmp/quantum_states.html'
fig.write_html(output_html)
print(f'<iframe src="{output_html}" width="100%" height="600" frameborder="0" allowfullscreen></iframe>')
