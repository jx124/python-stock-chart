import requests
import pandas as pd
import io
import matplotlib.pyplot as plt
import mplfinance as mpf

def parse_query(query_str):
    '''Parses input query string of the form &stock <ticker> <range> <interval> <type> <moving average values> and returns
    a dictionary containing tokens if successful.'''

    valid_ranges = ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max']
    valid_intervals = ['1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo']
    valid_types = ['candle', 'line']

    usage = '''Usage: &stock <ticker> <range> <interval> <type> <moving average values>. 
    E.g. &stock AAPL 1y 1d candle 2 3 5 creates a candlestick chart of AAPL for the last year at a daily 
    interval with 2, 3, and 5 day moving averages.'''
    
    query_tokens = query_str.strip().split(' ')
    
    # Input checks
    if not (query_tokens[0] == '&stock'):
        raise TypeError(usage)
    elif not query_tokens[2] in valid_ranges:
        raise TypeError('The valid ranges are: ' + str(valid_ranges))
    elif not query_tokens[3] in valid_intervals:
        raise TypeError('The valid intervals are: ' + str(valid_intervals))
    elif not query_tokens[4] in valid_types:
        raise TypeError('The valid types are: ' + str(valid_types))
    
    mav = query_tokens[5:]
    if mav:
        for value in mav:
            try:
                int(value)
            except Exception:
                raise TypeError("Invalid moving average values, try again with integers.")
        
    return {
        'ticker' : query_tokens[1].upper(),
        'range' : query_tokens[2],
        'interval' : query_tokens[3],
        'type' : query_tokens[4],
        'mav' : tuple(int(x) for x in query_tokens[5:])
    }

def request_data(tokens):
    '''Sends a query to Yahoo Finance for the stock data of the token. Returns a Pandas dataframe if successful.'''

    stock_url = 'https://query1.finance.yahoo.com/v7/finance/download/{}?' 
    headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0'}
    
    try:
        # Parameters for request
        params = {
            'range' : tokens['range'],
            'interval' : tokens['interval'],
            'events' : 'history',
        }

        response = requests.get(stock_url.format(tokens['ticker']), headers=headers, params=params)
        
        if response.status_code == 404:
            raise Exception("Error 404; please try again with another ticker/range/interval.")

        # Parse response into dataframe
        file = io.StringIO(response.text)
        return pd.read_csv(file, index_col=0, parse_dates=True)
    except Exception:
        raise

def create_chart(data, tokens):
    '''Creates stock chart from the data and tokens provided. Saves chart as image if successful.'''

    up_color = '#59eb00'    # Green
    down_color = '#FF0000'  # Red
    dc_gray = '#36393E'     # Discord's background gray

    # Sets the colors of the candlesticks, wicks, and volume bars
    mc = mpf.make_marketcolors(
        up = dc_gray,
        down = down_color,
        wick = {'up' : up_color, 'down' : down_color},
        edge = {'up' : up_color, 'down' : down_color},
        volume = {'up' : up_color, 'down' : down_color}
    )

    # Sets the colors of the background, text, and moving average lines
    s = mpf.make_mpf_style(
        marketcolors = mc, 
        base_mpl_style = 'dark_background',
        facecolor = dc_gray,
        figcolor = dc_gray,
        mavcolors = ['#5662f6', '#FFEB00', '#FF7A00', '#AEF35A', '#028910']
    )

    try:
        # Arguments for the plot function
        setup = {
            'type' : tokens['type'],
            'volume' : True,
            'tight_layout' : True,
            'style' : s,
            'mav' : tokens['mav'],
            'scale_width_adjustment' : {'lines' : 0.8, 'volume' : 0.65},
            'figscale' : 1,
            'figratio' : (10,5),
            'linecolor' : '#FFFFFF'
        }

        # Plot graph
        _fig, axes = mpf.plot(data, **setup, returnfig=True)

        # Select the correct plot
        ax = axes[0]
        # Set title containing the ticker, range, and interval
        ax.set_title(f"{tokens['ticker']} ({tokens['range']} Range, {tokens['interval']} Interval)")

        # Loops through the plotted moving average line (if any) to get the latest MA value, then displays it on the top left,
        # cycling through the available colors in "mavcolors" 
        if tokens['mav']:    
            for i, _line in enumerate(ax.lines):
                # Ignores the last line if a line chart is requested since that is the actual data
                if tokens['type'] == 'line' and i == len(ax.lines) - 1:
                    continue

                # Construct 'MA12: 345.67' string
                MA_string = f"MA{tokens['mav'][i]}: {ax.lines[i].get_ydata()[-1]:.2f}"
                # Places string with vertical offset for every MA line
                ax.text(0.02, 0.94-0.04*i, MA_string, transform=ax.transAxes, color=s["mavcolors"][i%len(s["mavcolors"])])
            
        # Save figure, 'tight' setting prevents labels from being cut off
        plt.savefig('stock.png', bbox_inches = 'tight')
        print('Complete')
    except Exception:
        raise

input_str = '&stock SPY 2y 1wk candle 5 10 20'
tokens = parse_query(input_str)

data = request_data(tokens)

create_chart(data, tokens)