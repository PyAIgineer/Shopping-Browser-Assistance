import streamlit as st
import asyncio
import json
import sys
import os
from PIL import Image
import requests
from io import BytesIO
import pandas as pd
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from product_research import EcommerceAgent  

st.set_page_config(
    page_title="Product Comparison Tool",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .product-card {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        background-color: #f9f9f9;
    }
    .source-amazon {
        color: #ff9900;
        font-weight: bold;
    }
    .source-flipkart {
        color: #2874f0;
        font-weight: bold;
    }
    .buy-button {
        background-color: #4CAF50;
        border: none;
        color: white;
        padding: 10px 24px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 8px;
    }
    .price {
        font-size: 1.2rem;
        font-weight: bold;
    }
    .product-name {
        font-size: 1.1rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Function to load and display image
def load_image(image_url):
    try:
        if image_url:
            response = requests.get(image_url)
            img = Image.open(BytesIO(response.content))
            return img
        return None
    except Exception as e:
        st.error(f"Error loading image: {e}")
        return None

# Function to run async code
def run_async(coroutine):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coroutine)
    finally:
        loop.close()

# Title and description
st.title("🔍 Product Comparison Tool")
st.markdown("""
This app searches for products on Amazon and Flipkart and helps you compare them side by side.
Enter a product name to see results from both platforms!
""")

# Search input
search_query = st.text_input("Enter product name to search", "")

# Sidebar for filters
st.sidebar.header("Filters")
show_amazon = st.sidebar.checkbox("Show Amazon Products", value=True)
show_flipkart = st.sidebar.checkbox("Show Flipkart Products", value=True)

# Sort options
sort_options = ["Price: Low to High", "Price: High to Low", "Rating: High to Low"]
sort_by = st.sidebar.selectbox("Sort By", sort_options)

# Function to normalize price string to a number
def normalize_price(price_str):
    if not price_str or price_str == "Not available":
        return float('inf')  # So items without price appear last when sorting by price
    # Extract just the numbers
    try:
        # Remove currency symbols and commas
        price_str = price_str.replace('₹', '').replace(',', '').replace('$', '').strip()
        # Find first number in the string
        import re
        price_match = re.search(r'\d+(\.\d+)?', price_str)
        if price_match:
            return float(price_match.group(0))
        return float('inf')
    except:
        return float('inf')

# Function to normalize rating string to a number
def normalize_rating(rating_str):
    if not rating_str or rating_str == "No rating":
        return 0
    try:
        # Extract numbers from string like "4.5 stars" or "4.5 out of 5"
        import re
        rating_match = re.search(r'(\d+\.\d+|\d+)', rating_str)
        if rating_match:
            return float(rating_match.group(0))
        return 0
    except:
        return 0

# Search button
if st.button("Search Products"):
    if search_query:
        with st.spinner(f"Searching for '{search_query}' on Amazon and Flipkart..."):
            # Initialize the EcommerceAgent class from PRF2
            ecommerce_agent = EcommerceAgent()
            
            # Run the search
            try:
                results = run_async(ecommerce_agent.search_all_products(search_query))
                
                if results["total_found"] == 0:
                    st.warning("No products found. Please try a different search term.")
                else:
                    st.success(f"Found {results['total_found']} products! ({results['amazon_count']} from Amazon, {results['flipkart_count']} from Flipkart)")
                    
                    # Filter products based on sidebar selections
                    filtered_products = []
                    for product in results["products"]:
                        if (product["source"] == "Amazon" and show_amazon) or \
                           (product["source"] == "Flipkart" and show_flipkart):
                            filtered_products.append(product)
                    
                    # Sort products
                    if sort_by == "Price: Low to High":
                        filtered_products.sort(key=lambda x: normalize_price(x.get("price", "Not available")))
                    elif sort_by == "Price: High to Low":
                        filtered_products.sort(key=lambda x: normalize_price(x.get("price", "Not available")), reverse=True)
                    elif sort_by == "Rating: High to Low":
                        filtered_products.sort(key=lambda x: normalize_rating(x.get("rating", "No rating")), reverse=True)
                    
                    # Display products in a grid
                    columns = 2  # Show products in 2 columns
                    rows = (len(filtered_products) + columns - 1) // columns  # Calculate number of rows needed
                    
                    for i in range(rows):
                        cols = st.columns(columns)
                        for j in range(columns):
                            idx = i * columns + j
                            if idx < len(filtered_products):
                                product = filtered_products[idx]
                                
                                # Determine source for styling
                                source_class = f"source-{product['source'].lower()}"
                                
                                with cols[j]:
                                    # Product card with expandable details
                                    with st.expander(f"{product['name'][:50]}...", expanded=False):
                                        st.markdown(f"<p class='product-name'>{product['name']}</p>", unsafe_allow_html=True)
                                        
                                        # Display product image if available
                                        if "image" in product and product["image"]:
                                            img = load_image(product["image"])
                                            if img:
                                                st.image(img, width=200)
                                        
                                        # Basic info
                                        col1, col2 = st.columns(2)
                                        with col1:
                                            st.markdown(f"<p class='price'>{product['price']}</p>", unsafe_allow_html=True)
                                            st.markdown(f"<p class='{source_class}'>Source: {product['source']}</p>", unsafe_allow_html=True)
                                        
                                        with col2:
                                            st.write(f"Rating: {product['rating']}")
                                            st.write(f"Reviews: {product['reviews']}")
                                        
                                        # Create a link for buy now button
                                        link = product.get("link", "#")
                                        if not link or link == "#":
                                            if product["source"] == "Amazon":
                                                link = f"https://www.amazon.in/s?k={product['name'].replace(' ', '+')}"
                                            elif product["source"] == "Flipkart":
                                                link = f"https://www.flipkart.com/search?q={product['name'].replace(' ', '+')}"
                                        
                                        st.markdown(f"<a href='{link}' target='_blank'><button class='buy-button'>Buy Now</button></a>", unsafe_allow_html=True)
                    
                    # Add a comparison table
                    st.subheader("Quick Comparison")
                    comparison_data = []
                    for product in filtered_products:
                        comparison_data.append({
                            "Product": product['name'][:50] + "...",
                            "Price": product['price'],
                            "Rating": product['rating'],
                            "Source": product['source']
                        })
                    
                    if comparison_data:
                        comparison_df = pd.DataFrame(comparison_data)
                        st.dataframe(comparison_df, use_container_width=True)
                    
            except Exception as e:
                st.error(f"Error occurred during search: {str(e)}")
                st.error("Please check your backend code and make sure it's running correctly.")
    else:
        st.warning("Please enter a search term")

# Add information about the app
st.sidebar.markdown("---")
st.sidebar.header("About")
st.sidebar.info("""
This app compares products from Amazon and Flipkart to help you make better shopping decisions. 
The data is scraped in real-time from both websites.
""")

# How to use section in sidebar
st.sidebar.header("How to Use")
st.sidebar.markdown("""
1. Enter a product name in the search box
2. Click 'Search Products' button
3. Expand product cards to see details
4. Click 'Buy Now' to go to the product page
5. Use filters in the sidebar to refine results
""")