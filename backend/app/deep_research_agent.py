from dotenv import load_dotenv
import os
from collections import Counter
from typing import Optional, TypedDict, Annotated, List, Literal
from playwright.async_api import Page, Locator
from operator import add
from pydantic import BaseModel, Field
from Browser.webrover_browser import WebRoverBrowser
from playwright.async_api import async_playwright
import asyncio
import platform
from langchain_text_splitters import NLTKTextSplitter, SpacyTextSplitter
from newspaper import Article
import aiohttp
import asyncio
import re
from io import BytesIO
from langchain_core.output_parsers import StrOutputParser
import json
from datetime import datetime
from dateutil import parser
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from io import BytesIO
from PyPDF2 import PdfReader
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import START, END, StateGraph
from IPython.display import Image, display
from langchain_huggingface import HuggingFaceEmbeddings
import nltk
from urllib.parse import urlparse

#nltk.download('punkt')

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")


os.environ["CHROMA_TELEMETRY_ENABLED"] = "false"
load_dotenv()
def set_env_vars(var):
    value = os.getenv(var)
    if value is not None:
        os.environ[var] = value


vars = ["GEMINI_API_KEY", "LANGCHAIN_API_KEY", "LANGCHAIN_TRACING_V2", "LANGCHAIN_ENDPOINT", "LANGCHAIN_PROJECT", "TAVILY_API_KEY"]

for var in vars:
    set_env_vars(var)


llm_flash_lite = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0,api_key=os.getenv("GEMINI_API_KEY"))
llm_flash = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0,api_key=os.getenv("GEMINI_API_KEY"))
llm_pro = ChatGoogleGenerativeAI(model="gemini-2.5-pro", temperature=0,api_key=os.getenv("GEMINI_API_KEY"))


class SourceQuality(BaseModel):
    """Assessment of source credibility and academic value"""
    domain_type: Literal["academic", "government", "news", "commercial", "other"]
    credibility_score: float = Field(ge=0, le=1, description="0-1 credibility rating")
    peer_reviewed: bool = False
    publication_date: Optional[str] = None
    author_credentials: Optional[str] = None
    citation_count: Optional[int] = None
    methodology_quality: Optional[str] = None


class ResearchGap(BaseModel):
    """Identification of research gaps"""
    gap_type: Literal["empirical", "theoretical", "methodological", "practical"]
    description: str
    importance: Literal["high", "medium", "low"]
    suggested_approach: str

class CitationNetwork(BaseModel):
    """Citation and reference network analysis"""
    key_authors: List[str]
    seminal_papers: List[str]
    recent_developments: List[str]
    conflicting_findings: List[str]


class MethodologicalFramework(BaseModel):
    """Research methodology assessment"""
    research_paradigm: Literal["quantitative", "qualitative", "mixed_methods", "theoretical"]
    data_collection_methods: List[str]
    analysis_techniques: List[str]
    limitations: List[str]
    validity_concerns: List[str]


class Url(BaseModel):
    url: str | Literal["NO_CHANGE"] = Field(description="The url to navigate to")

class SelfReview(BaseModel):
    answer: Literal["Yes", "No"]
    reasoning: str
    
class DomElement(TypedDict):
    index : int
    text : str
    type : str
    xpath : str
    x: float
    y: float
    description : str


class Action(TypedDict):
    thought : str
    action_type : Literal["click", "type", "scroll_read", "close_page", "wait", "go_back", "go_to_search", "retry"]
    args : str 
    action_element : DomElement



class SubtopicState(BaseModel):
    subtopics: List[str]

class SubtopicAnswer(BaseModel):
    subtopic: str
    subtopic_answer: str
    methodology: MethodologicalFramework
    research_gaps: List[ResearchGap]
    citation_network: CitationNetwork
    source_quality_assessment: List[SourceQuality]
    key_findings: List[str]
    contradictions: List[str]
    references: List[str]

    
class FinalAnswerComponents(BaseModel):
    introduction: str
    conclusion: str
    references: str | List[str] = Field(description="List of all the references used in all the subtopic answers")


class AgentState(TypedDict):
    input: str
    page : Page
    dom_elements : List[DomElement]
    action : Action
    actions_taken : Annotated[List[str], add]
    visited_urls : Annotated[List[str], add]
    conversation_history: Annotated[List[str], add]
    new_page: Literal[True, False]
    subtopic_answers: Annotated[List[SubtopicAnswer], add]
    final_answer: str
    is_pdf: Literal[True, False]
    subtopics: List[str]
    subtopic_status: Annotated[List[str], add]
    subtopic_to_research: str
    number_of_urls_visited: int
    collect_more_info: Literal[True, False]



async def setup_browser(go_to_page: str):
    print(f"Setting up browser for {go_to_page}")
    browser = WebRoverBrowser()
    browser, context = await browser.connect_to_chrome()

    page = await context.new_page()
    
    try:
        await page.goto(go_to_page, timeout=80000, wait_until="domcontentloaded")
    except Exception as e:
        print(f"Error loading page: {e}")
        # Fallback to Google if the original page fails to load/
        
        await page.goto("https://www.google.com", timeout=100000, wait_until="domcontentloaded")

    return browser, page


# Screen Annotations
from playwright.async_api import async_playwright
import asyncio

# Load the JavaScript file
with open("marking_scripts/final_marking.js", "r", encoding="utf-8") as f:
    marking_script = f.read()

async def execute_script(page):

    await asyncio.sleep(3)
    
    # Run the JavaScript marking function
    dom_tree = await page.evaluate(f"""
        (function() {{
            {marking_script}
            return captureInteractiveElements();
        }})();
    """)

        
    return dom_tree

async def remove_highlights(page):

    await asyncio.sleep(1)
    # Ensure the function is executed properly
    await page.evaluate("""
        (function() {
            if (typeof unmarkElements === 'function') {
                unmarkElements();
            } else {
                console.error('unmarkElements() not found. Re-injecting...');
                (function() {
                    function unmarkElements() {
                        console.log("Removing highlights...");

                        // Remove highlight container
                        const highlightContainer = document.getElementById('web-agent-highlight-container');
                        if (highlightContainer) {
                            highlightContainer.remove();
                            console.log("Highlight container removed.");
                        }

                        // Remove all highlight overlays
                        document.querySelectorAll("div").forEach(el => {
                            const style = window.getComputedStyle(el);
                            if (
                                (el.id && el.id.includes("highlight")) || 
                                style.border.includes("2px solid") || 
                                style.backgroundColor.includes("22") || 
                                style.zIndex === "2147483647"
                            ) {
                                el.remove();
                            }
                        });

                        // Remove lingering elements
                        setTimeout(() => {
                            document.querySelectorAll("[id^='highlight-'], div[style*='border: 2px solid'], div[style*='z-index: 2147483647']")
                                .forEach(el => el.remove());
                        }, 100);
                    }

                    unmarkElements();
                })();
            }
        })();
    """)



# Click

async def click(state: AgentState):
    page = state["page"]
    element_type = state["action"]["action_element"]["type"]
    try:    
        xpath = state["action"]["action_element"]["xpath"]
    except Exception as e:
        bbox_x = state["action"]["action_element"]["x"]
        bbox_y = state["action"]["action_element"]["y"]

    # Scroll the element into view using its XPath
    try:
        await page.evaluate(
            """
            (xpath) => {
                const result = document.evaluate(
                    xpath, 
                    document, 
                    null, 
                    XPathResult.FIRST_ORDERED_NODE_TYPE, 
                    null
                );
                const element = result.singleNodeValue;
                if (element) {
                    element.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'nearest' });
                }
            }
            """,
            xpath
        )
    except Exception as e:
        return {
            "actions_taken": ["Failed to scroll element into view, retrying..."],
            "page": state["page"],
            "new_page": False
        }

    try:
        element = page.locator(f'xpath={xpath}')
        if element_type == "link":
            try:
                async with page.context.expect_page(timeout=10000) as new_page_info:
                    if platform.system() == "Darwin":
                        await element.click(modifiers=["Meta"], timeout=5000)
                    else:
                        await element.click(modifiers=["Control"], timeout=5000)
                    
                try:
                    new_page = await new_page_info.value
                    if new_page:
                        await new_page.bring_to_front()
                        await new_page.wait_for_load_state("domcontentloaded", timeout=10000)
                        state["page"] = new_page
                    else:
                        return {
                            "actions_taken": ["Link click didn't open new page, retrying..."],
                            "page": state["page"],
                            "new_page": False
                        }
                except TimeoutError:
                    return {
                        "actions_taken": ["Page load timed out, retrying..."],
                        "page": state["page"],
                        "new_page": False
                    }
            except TimeoutError:
                # Fallback to coordinate-based clicking if element click times out
                return {
                    "actions_taken": ["Element click timed out, retrying with coordinates..."],
                    "page": state["page"],
                    "new_page": False
                }
        else:
            await element.click(timeout=5000)

    except Exception as fallback:
        # Coordinate-based clicking fallback
        try:
            bbox_x = state["action"]["action_element"]["x"]
            bbox_y = state["action"]["action_element"]["y"]
            
            if element_type == "link":
                try:
                    async with page.context.expect_page(timeout=10000) as new_page_info:
                        if platform.system() == "Darwin":
                            await page.keyboard.down("Meta")
                            await page.mouse.click(bbox_x, bbox_y, click_count=3)
                            await page.keyboard.up("Meta")
                        else:
                            await page.keyboard.down("Control")
                            await page.mouse.click(bbox_x, bbox_y, click_count=3)
                            await page.keyboard.up("Control")
                        
                        try:
                            new_page = await new_page_info.value
                            if new_page:
                                await new_page.bring_to_front()
                                await new_page.wait_for_load_state("domcontentloaded", timeout=10000)
                                state["page"] = new_page
                            else:
                                return {
                                    "actions_taken": ["Coordinate click didn't open new page, retrying..."],
                                    "page": state["page"],
                                    "new_page": False
                                }
                        except TimeoutError:
                            return {
                                "actions_taken": ["Page load timed out after coordinate click, retrying..."],
                                "page": state["page"],
                                "new_page": False
                            }
                except TimeoutError:
                    return {
                        "actions_taken": ["Coordinate click timed out, retrying..."],
                        "page": state["page"],
                        "new_page": False
                    }
            else:
                await page.mouse.click(bbox_x, bbox_y)
        except Exception as e:
            await page.evaluate("""
                async () => {
                    const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
                    
                    // Scroll back to the top after scrolling down
                    window.scrollTo({ top: 0, left: 0, behavior: 'smooth' });
                    
                    // Wait until the scroll position reaches the top
                    while (window.scrollY > 0) {
                        await delay(100);
                    }
                }
                """)
            return {
                "actions_taken": ["All click attempts failed, retrying..."],
                "page": state["page"],
                "new_page": False
            }

    await asyncio.sleep(2)
    
    element_description = (
        f"{state['action']['action_element']['type']} element "
        f"{state['action']['action_element']['description']}"
    )
    
    if state["page"] == page:
        return {"actions_taken": [f"Clicked {element_description}"], "page": state["page"], "new_page": False}
    else:
        return {"actions_taken": [f"Clicked {element_description}"], "page": state["page"], "new_page": True}


# After Click Router

async def after_click_router(state: AgentState):
    if state["new_page"]:
        return "scroll_and_read"
    else:
        return "annotate_page"
    

# Type

async def type(state: AgentState):
    """Types text into an input field located by its XPath, fallback bounding box if XPath fails."""
    page = state["page"]
    text = state["action"]["args"]
    
    
        
    try:
        bbox_x, bbox_y = state["action"]["action_element"]["x"], state["action"]["action_element"]["y"]
        await page.mouse.click(bbox_x, bbox_y, click_count=3)
        await asyncio.sleep(1)
        select_all = "Meta+A" if platform.system() == "Darwin" else "Control+A"
        await page.keyboard.press(select_all)
        await asyncio.sleep(1)
        await page.keyboard.press("Backspace")
        await asyncio.sleep(1)
        await page.keyboard.type(text)
        await asyncio.sleep(4)

    except Exception as e:
        xpath = state["action"]["action_element"]["xpath"]
        await page.locator(f'xpath={xpath}').click()
        await asyncio.sleep(1)
        select_all = "document.execCommand('selectAll', false, null);"
        await page.locator(f'xpath={xpath}').evaluate(select_all)
        await asyncio.sleep(1)
        await page.locator(f'xpath={xpath}').type(text)
        await asyncio.sleep(4)
        

    element_description = f"{state['action']['action_element']['type']} element {state['action']['action_element']['description']}"
    await page.keyboard.press("Enter")
    await asyncio.sleep(2)
    
    return {"actions_taken": [f"Typed {text} into {element_description}"]}


# Scroll Page 

async def scroll_page(state: AgentState):
    """Smoothly scrolls down until either the bottom of the page is reached or 10 scroll events have occurred, then scrolls back to the top."""
    page = state["page"]

    print(page.url)
    await page.evaluate("""
    async () => {
        const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
        let scrollCount = 0;
        
        // Scroll down until the bottom is reached or maximum 10 scrolls have been performed
        while (scrollCount < 10 && (window.innerHeight + window.scrollY) < document.body.scrollHeight) {
            window.scrollBy({ top: 650, left: 0, behavior: 'smooth' });
            scrollCount++;
            await delay(350);
        }
        
        // Scroll back to the top after scrolling down
        window.scrollTo({ top: 0, left: 0, behavior: 'smooth' });
        
        // Wait until the scroll position reaches the top
        while (window.scrollY > 0) {
            await delay(100);
        }
    }
    """)

    return {"actions_taken": [f"Scrolled down the page and collected information"]}


# Scroll pdf

async def scroll_pdf(state: AgentState):
    page = state["page"]
    # Click to ensure the PDF viewer is focused
    await page.mouse.click(300, 300)
    
    # Use smaller scroll increments for smoother scrolling.
    # For instance, scroll 100 pixels at a time, 50 times.
    for _ in range(50):
        await page.mouse.wheel(0, 300)
        await asyncio.sleep(0.1)

    for _ in range(10):
        await page.mouse.wheel(0, -1500)
        await asyncio.sleep(0.1)
    
    # Optionally, scroll back to the top.
    await page.evaluate("window.scrollTo({ top: 0, behavior: 'smooth' })")
    return {"actions_taken": ["Scrolled PDF viewer and collected the relevant information"]}

# Close Page

async def close_page(state: AgentState):
    context = state["page"].context  # Get the browser context from the current page
    await state["page"].close()        # Close the current tab
    page = context.pages[-1] 
    print(page.url)
    return {"actions_taken": [f"Closed the current tab and switched to the last opened tab"], "page": page}


# Close Opened Link

async def close_opened_link(state: AgentState):
    current_url = state["page"].url
    context = state["page"].context  # Get the browser context from the current page
    await state["page"].close()        # Close the current tab
    page = context.pages[-1] 
    await page.evaluate("""
    async () => {
        const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
        // Scroll back to the top after scrolling down
        window.scrollTo({ top: 0, left: 0, behavior: 'smooth' });
                        
        // Wait until the scroll position reaches the top
        while (window.scrollY > 0) {
            await delay(100);
        }
    }
    """)
    print(page.url)
    return {"actions_taken": [f"Closed the opened link {current_url} and switched to {page.url}"], "page": page}


# Wait

async def wait(state: AgentState):
    """Waits for a specified amount of time."""
    seconds = state["action"]["args"]
    await asyncio.sleep(5)
    return {"actions_taken": [f"Waited for {seconds} seconds"]}


# Go Back 

async def go_back(state: AgentState):
    """Goes back to the previous page by calling window.history.back() and waiting for a known element."""
    page = state["page"]
    # Trigger back navigation via JavaScript.
    previous_page = page.url
    await page.evaluate("window.history.back()")
    # Wait a bit for the navigation to complete.
    # Optionally, you can wait for a specific selector you expect on the previous page:
    # await page.wait_for_selector("css=selector-of-known-element", timeout=30000)
    await page.wait_for_timeout(5000)
    current_page = page.url
    return {"actions_taken": [f"Navigated back to {current_page} from {previous_page}"]}



# Go to Search 

async def go_to_search(state: AgentState):
    """Goes to google.com"""
    page = state["page"]
    await page.goto("https://www.google.com", timeout=30000, wait_until="domcontentloaded")
    return {"actions_taken": [f"Navigated to Google"]}

# Scrape Text
def extract_text_from_html(html_content):
    """Extract clean text from HTML"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'advertisement']):
            element.decompose()
        
        # Try different content selectors in order of preference
        content_selectors = [
            # Academic paper selectors
            '.ltx_document', '.paper-content', '.full-text', '.article-text',
            # General article selectors  
            'article', 'main', '.content', '.post-content', '.entry-content',
            '.article-body', '.story-body', '.text-content', '.main-text',
            # Fallback selectors
            '#content', '#main-content', '.main-content', '.container'
        ]
        
        text = ""
        for selector in content_selectors:
            elements = soup.select(selector)
            if elements:
                text = '\n'.join([elem.get_text(separator=' ', strip=True) for elem in elements])
                if len(text.strip()) > 100:  # Only use if substantial content
                    break
        
        # If no specific content found, try body
        if not text or len(text.strip()) < 100:
            body = soup.find('body')
            if body:
                text = body.get_text(separator=' ', strip=True)
        
        # Clean up text
        if text:
            # Remove excessive whitespace
            text = re.sub(r'\s+', ' ', text)
            # Remove common boilerplate
            text = re.sub(r'(cookies?|privacy policy|terms of service|subscribe|newsletter).*?(?=\.|$)', '', text, flags=re.IGNORECASE)
            # Clean up
            text = text.strip()
        
        return text if text and len(text.strip()) > 50 else ""
        
    except Exception as e:
        return ""
async def scrape_text(page):
    """Enhanced text scraping with multiple extraction methods"""
    url = page.url
    
    # Method 1: Try newspaper3k first
    try:
        article = Article(url)
        article.download()
        article.parse()
        
        if article.text and len(article.text.strip()) > 50:
            return article.text
    except:
        pass
    
    # Method 2: Direct HTML scraping with BeautifulSoup
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    text = extract_text_from_html(html)
                    if text and len(text.strip()) > 50:
                        return text
    except:
        pass
    
    # Method 3: Try to get content directly from the page object if it has HTML
    try:
        if hasattr(page, 'content'):
            text = extract_text_from_html(page.content())
            if text and len(text.strip()) > 50:
                return text
    except:
        pass
    
    return "No data found"
    
# Scrape PDF

async def scrape_pdf(page):
    """Enhanced PDF scraping"""
    url = page.url
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return "Forbidden"
                
                content = await response.read()
                
                # Check if it's actually a PDF
                if not content.startswith(b'%PDF'):
                    return "Not a valid PDF file"
                
                # Extract text from PDF
                try:
                    pdf_data = BytesIO(content)
                    reader = PdfReader(pdf_data)
                    
                    if len(reader.pages) == 0:
                        return "No data found"
                    
                    text_parts = []
                    for page_num in range(len(reader.pages)):
                        try:
                            page_obj = reader.pages[page_num]
                            page_text = page_obj.extract_text()
                            if page_text and page_text.strip():
                                # Clean up common PDF extraction issues
                                page_text = re.sub(r'(\w)-\s*\n(\w)', r'\1\2', page_text)  # Fix hyphenated words
                                page_text = re.sub(r'\s+', ' ', page_text)  # Normalize whitespace
                                text_parts.append(page_text.strip())
                        except Exception:
                            continue  # Skip problematic pages
                    
                    full_text = '\n'.join(text_parts)
                    
                    if not full_text.strip():
                        return "No data found"
                    
                    return full_text
                    
                except Exception as e:
                    return "Forbidden"
                    
    except Exception as e:
        return "Forbidden"
# Docs from Text

async def docs_from_text(data, url):
    text_splitter = NLTKTextSplitter(chunk_size=1200, chunk_overlap=50)
    texts = text_splitter.split_text(data)

    # Dummy title extraction (can use page.title or OpenGraph scraping later)
    title = url.split("/")[-1].replace("-", " ").replace(".html", "").title()
    domain = urlparse(url).netloc

    docs = [
        Document(
            page_content=text,
            metadata={"source": url, "title": title, "domain": domain}
        ) for text in texts
    ]
    return docs


async def store_doc_embeddings(docs):


    vector_store = Chroma(
        collection_name="webpage_rag",
        embedding_function=embeddings,
        persist_directory="./rag_store_webpage",  # Where to save data locally, remove if not necessary
    )

    vector_store.add_documents(docs)

async def web_page_rag(state: AgentState):
    """Searches the web page for relevant information based on the User input"""
    page = state["page"]

    if state["is_pdf"]:
        result = await scrape_pdf(page)
    else:
        result = await scrape_text(page)

    if result == "Forbidden":
        return {"actions_taken": [f"Scraping the webpage {page.url} failed, should try another url"]}
    elif result == "No data found":
        return {"actions_taken": [f"No textual content found on the webpage {page.url}, try looking for url that has data"]}
    else:
        docs = await docs_from_text(result, page.url)
        print(len(docs))

        await store_doc_embeddings(docs)

        return {"actions_taken":[f"Scraped the url {page.url} and stored the information in a vector database for future reference"]}


async def note_scroll_read(state: AgentState):
    page = state["page"]
   
    url = str(page.url)

    visited_urls = state.get("visited_urls", [])

    if url in visited_urls:
        return state
    else:
        return {"visited_urls": [url]}


# URL Decide Node

async def url_decide_node(state: AgentState):
    input = state["input"]
    if not state.get("subtopic_to_research"):
        return {"page": state["page"]}

    system_message = """
    You are the navigation strategist for a deep research agent.
    Your role is to decide the *most effective* next URL to visit to advance the research task.

    You will be given:
    - The current research task.
    - Conversation history.
    - The current page's URL.

    You must select the most logical destination URL for the next step in research.

    ## Core Principles
    1. **Topic Continuity**
       - If the task is a continuation of the same research topic and the current site is still useful, return "NO_CHANGE".

    2. **Source Prioritization**
       - For factual or academic research → prefer high-authority sources first (Google Scholar, government sites, reputable news, Wikipedia for orientation).
       - For technical topics → consider documentation sites, GitHub, standards pages.
       - For data gathering → use credible databases or search engines.

    3. **Specific vs. General Tasks**
       - If the user asks for info only available on one known site → go directly there.
       - If the task can be completed on many possible sites → go to a general search engine first to compare options.

    4. **Deep Research Behavior**
       - Break down vague tasks into subtopics and choose URLs that provide the best next piece of knowledge.
       - Avoid random site changes — always move in a logical sequence that builds towards answering the research question.
       - Prefer URLs that are one step closer to *final actionable information*.

    5. **Efficiency**
       - Do not redirect to the same site unnecessarily.
       - Avoid sources with low credibility unless explicitly requested.

    Note: While returning the url, return the url in the format of the url and no text associated with it.
    """

    human_prompt = """
    This is the task provided by the user: {input}
    This is the conversation history: {conversation_history}
    This is the current page url: {page_url}
    """

    input = state["input"]
    conversation_history = state.get("conversation_history", [])
    page = state["page"]

    human_message = human_prompt.format(input=input, conversation_history=conversation_history, page_url=page.url)

    messages = [
        SystemMessage(content=system_message),
        HumanMessage(content=human_message)
    ]

    structured_llm = llm_flash.with_structured_output(Url)
    response = structured_llm.invoke(messages)
    print(response)

    page = state["page"]
   

    if response.url == "NO_CHANGE":
        return {"page": page }
    else:
        await page.goto(response.url)
        return { "page": page }
    


async def topic_breakdown(state: AgentState):
    system_message = """ 
    You are an expert at breaking down a topic into smaller subtopics.
    You will be given a topic and you will need to break it down 3-6 smaller subtopics.

    Make sure the subtopics are concise enough to be used as a search query.
    Avoid redundancy and overlap.
    Maintain a logical order from general understanding to deeper, specialized aspects.
    """

    human_prompt = """
    This is the topic: {topic}
    """

    input = state["input"]

    human_message = human_prompt.format(topic=input)

    messages = [
        SystemMessage(content=system_message),
        HumanMessage(content=human_message)
    ]

    response = llm_flash.with_structured_output(SubtopicState).invoke(messages)
    
    return {
        "subtopics": response.subtopics,
        "research_depth_level": 1,
        "current_search_strategy": "comprehensive"
    }





async def track_subtopic_status(state: AgentState):

    system_message = """ 
        You are an expert at tracking the status of research for a given list of subtopics.

        - You will be given a list of subtopics and their corresponding research statuses.
        - If the status is empty, it means no research has been done for any subtopic.
        - If some subtopics have been researched, determine the next subtopic that needs research.
        - If all subtopics have been researched, return "ALL_DONE".
        - Always prioritize selecting the first subtopic in the list that has not been researched yet.

        Important Notes:
        - Only return the name of the next subtopic that requires research.
        - Do not return "ALL_DONE" unless all subtopics have been researched.
        - Ensure logical prioritization: the next subtopic should be chosen based on list order.

        Example:
        - Subtopics: ["AI in Healthcare", "AI in Finance", "AI in Education"]
        - Subtopic Status: ["AI in Healthcare Completed", "", ""]
        - Expected Output: AI in Finance
    """

    human_prompt = """
    This is the list of subtopics: {subtopics}
    This is the status of the research completed for each subtopic: {subtopic_status}
    """

    subtopics = state["subtopics"]
    subtopic_status = state.get("subtopic_status", [])

    human_message = human_prompt.format(subtopics=subtopics, subtopic_status=subtopic_status)

    messages = [
        SystemMessage(content=system_message),
        HumanMessage(content=human_message)
    ]

    response = llm_flash.invoke(messages)

    return {"subtopic_to_research": response.content}
    


async def research_router(state: AgentState):
    subtopic_to_research = state["subtopic_to_research"]

    if subtopic_to_research == "ALL_DONE":
        return "compile_research"
    else:
        return "go_to_search"
    

async def annotate_page(state: AgentState):
    page = state["page"]
    
    dom_elements = await execute_script(page)

    await remove_highlights(page)

    if dom_elements[0]["type"] == "pdf":
        return {"dom_elements": dom_elements, "is_pdf": True}
    else:
        return {"dom_elements": dom_elements, "is_pdf": False}




async def llm_call_node(state: AgentState):

    template = """ 
    You are AgentR, an autonomous DEEP RESEARCH web agent. 
    You browse, interact, and extract information from authoritative sources to fulfill the user’s research goal.
    
    ## Your Tools
    - **Click Elements**: Click links/buttons by XPath. For links, open in a new tab.
    - **Type in Inputs**: Enter/refine search queries or form data.
    - **Scroll and Read (Scrape+RAG)**: Scroll to reveal and store relevant content.
    - **Close Page**: Close current tab and return to the last tab.
    - **Go Back**: Return to previous page.
    - **Go to Search**: Navigate to Google.
    - **Wait**: Pause for page loading.
    - **Retry**: Use only when no clear next action exists.
    
    ## Research Principles
    1. **Focus** on the user’s subtopic — avoid drifting into irrelevant areas.
    2. **Prioritize authoritative, high-quality sources** (.edu, .gov, peer-reviewed, reputable news).
    3. **Avoid repeats** — do not retry the same search/query/action unless refined.
    4. **Diversify sources** — seek multiple perspectives.
    5. **Cross-reference facts** — avoid relying on a single source.
    6. **Progress logically** — each action should bring you closer to the final answer.
    
    ## Action Selection Rules
    - If there is a relevant, high-quality link → Click it (only if URL not visited before).
    - If you can refine or improve a search → Type in Inputs.
    - If there is valuable info on the page without links → Scroll and Read.
    - If stuck after 3 similar actions → Change strategy (new query, new source).
    - If lost or off-track → Go Back or Go to Search.
    
    ## Output Requirements
    Return **one coherent action or sequence**:
    - Thought: Why you chose this action now.
    - Action: The next step.
    - DOM Element (if applicable): The exact element to interact with.
    - Reasoning: Step-by-step rationale tied to research progress.
    - Never repeat an unproductive search term — modify or try alternatives.
    """



    prompt = ChatPromptTemplate(
    messages=[
        ("system", template),
        ("human", "Input: {input}"),
        ("human", "Actions Taken So far: {actions_taken}"),
        ("human", "Interactive Elements: {dom_elements}"),
        ("human", "Urls Already Visited: {visited_urls}"),
        ("human", "Alternative Search Queries Available: {alt_queries}"),
        
    ],
    input_variables=["input", "dom_elements", "actions_taken"],
    partial_variables={"actions_taken": [], "visited_urls": [], "alt_queries": []},
    optional_variables=["actions_taken", "visited_urls", "alt_queries"]
    )


    actions_taken = state.get("actions_taken", [])
    dom_elements = state["dom_elements"]
    input = state["subtopic_to_research"]
    visited_urls = state.get("visited_urls", [])
    alt_queries = state.get("alternative_queries", [])
    prompt_value = prompt.invoke({"actions_taken": actions_taken, "dom_elements": dom_elements, "input": input, "visited_urls": visited_urls,"alt_queries": alt_queries})

    response = llm_pro.with_structured_output(Action).invoke(prompt_value)

    action = response
    # Ensure action_element is always a dict
    #if action.get("action_element") is None:
        #action["action_element"] = {}

    return {"action": action}



tools = {
    "click" : "click",
    "type" : "type",
    "scroll_read" : "scroll_and_read",
    "close_page" : "close_page",
    "wait" : "wait",
    "go_back" : "go_back",
    "go_to_search" : "go_to_search",
}

def tool_router(state: AgentState):
    action = state["action"]
    action_type = action["action_type"]

    if action_type == 'retry':
        return "annotate_page"
    
    return tools[action_type]


async def scroll_and_read(state: AgentState):

    page = state["page"]
    await page.wait_for_load_state("domcontentloaded")
    
    page = state["page"]
    result = await page.evaluate("""
        () => {
            const url = window.location.href.toLowerCase();
            const isPDF = url.endsWith('.pdf') ||
                document.querySelector("embed[type*='pdf']") ||
                document.querySelector("iframe[src*='.pdf']");
                
            if (isPDF) {
                return "pdf";
            } else {
                return "webpage";
            }
        }
    """)
    return { "is_pdf": result == "pdf" }


async def webpage_or_pdf(state: AgentState):
    is_pdf = state["is_pdf"]

    if is_pdf:
        return "scroll_pdf"
    else:
        return "scroll_page"



async def self_review(state: AgentState):
    vector_store = Chroma(
    collection_name="webpage_rag",
    embedding_function=embeddings,
    persist_directory="./rag_store_webpage",
)

    input_text = state["subtopic_to_research"]
    relevant_docs = vector_store.similarity_search(input_text, k=40)

    print(f"Number of documents: {len(relevant_docs)}")

    system_message = """
    You are an expert at reviewing a set of relevant documents related to the user's query and deciding if the information is sufficient to answer the user's query.
    You will be given a user's query and a set of relevant documents.
    Answer only in the format of "Yes" or "No".

    Also state the reason for your answer.
    """

    human_prompt = """
    This is the user's query: {input}
    This is the set of documents: {relevant_docs}
    """

    human_message = human_prompt.format(input=input_text, relevant_docs=relevant_docs)

    messages = [
        SystemMessage(content=system_message),
        HumanMessage(content=human_message)
    ]

    structured_llm = llm_flash.with_structured_output(SelfReview)
    response = structured_llm.invoke(messages)


    if response.answer == "Yes":
        if response.answer == "Yes":
            state["actions_taken"] = response.reasoning
        return {"actions_taken" : [f"I have enough information on {input_text}. I will now proceed to write the article on {input_text}"], "collect_more_info" : False}
    else:
        return {"actions_taken" : [f"I need more information on {input_text}. I should visit more websites to gather  information on {input_text}"], "collect_more_info" : True}




async def after_self_router(state: AgentState):
    collect_more_info = state["collect_more_info"]
    if collect_more_info:
        return "annotate_page"
    else:
        return "subtopic_answer_node"

def format_references(docs: list[Document]) -> str:
    seen = set()
    refs = []
    for doc in docs:
        url = doc.metadata.get("source", "Unknown URL")
        title = doc.metadata.get("title", "Untitled")
        domain = doc.metadata.get("domain", "Unknown Source")
        key = f"{title}|{url}"
        if key in seen:
            continue
        seen.add(key)
        refs.append(f"{title}. Retrieved from {url} ({domain})")
    return "\n".join(refs)

# Updated subtopic_answer_node with formatted references

async def subtopic_answer_node(state: AgentState):
    vector_store = Chroma(
        collection_name="webpage_rag",
        embedding_function=embeddings,
        persist_directory="./rag_store_webpage",
    )

    input_text = state["subtopic_to_research"]
    relevant_docs = vector_store.similarity_search(input_text, k=60)
    formatted_references = format_references(relevant_docs)

    system_message = """
    You are a senior research analyst writing a section for a high-level research report.

    Your job:
    - Synthesize information from all provided sources into a coherent, well-structured section.
    - Use only the given documents — no outside information or invented facts.
    - Identify the most important insights, trends, examples, and debates in the topic.
    - Integrate multiple perspectives, noting agreements, contradictions, and gaps in knowledge.
    - Use precise, evidence-backed language — avoid vague claims.
    - Adapt length to the complexity of the topic; be as detailed as the evidence allows.
    - Maintain a professional, academic tone that is still readable.
    - Clearly attribute all factual claims to the provided references.
    - Conclude with key takeaways that connect this subtopic to the larger research goal.

    Structure recommendation (adapt as needed):
    1. Introduction : Define and briefly contextualize the subtopic.
    2. Key Insights : Present main themes, each backed by multiple sources where possible.
    3. Contrasting Perspectives / Challenges : Highlight disagreements or limitations.
    4. Implications / Future Outlook : Suggest what these findings mean going forward.
    5. References : Only list provided sources, in APA or similar academic style.
    """

    human_prompt = """
    Subtopic: {input}
    Main research topic: {main_topic}

    Relevant source excerpts:
    {relevant_docs}

    Reference list for citations:
    {formatted_references}

    Write a comprehensive, academically rigorous section on this subtopic.
    """

    human_message = human_prompt.format(
        input=input_text,
        main_topic=state["input"],
        relevant_docs="\n\n".join([doc.page_content[:500] for doc in relevant_docs]),
        formatted_references=formatted_references
    )

    messages = [
        SystemMessage(content=system_message),
        HumanMessage(content=human_message)
    ]

    response = llm_pro.with_structured_output(SubtopicAnswer).invoke(messages)

    return {
        "subtopic_answers": [response],
        "subtopic_status": [f"Comprehensive research on {input_text} completed"],
        "actions_taken": [f"Generated high-quality academic section on {input_text}"]
    }


async def empty_rag_store(state : AgentState):

    vector_store = Chroma(
    collection_name="webpage_rag",
    embedding_function=embeddings,
    persist_directory="./rag_store_webpage",
    )

    try:
        client = vector_store._client  # Access the underlying Chroma client
        client.delete_collection("webpage_rag")
        return {"actions_taken" : ["Emptied Vector Store"]}

    except Exception as e:
        print(f"Error deleting collection: {e}")
        return {"actions_taken" : ["Error Emptying Vector Store"]}



# Stuck Prevention System
class StuckDetector:
    def __init__(self):
        self.action_history = []
        self.stuck_threshold = 5
        
    def is_stuck(self, current_action: str) -> bool:
        self.action_history.append(current_action)
        
        # Keep only recent actions
        if len(self.action_history) > 10:
            self.action_history = self.action_history[-10:]
        
        # Check for repetitive patterns
        if len(self.action_history) >= self.stuck_threshold:
            recent_actions = self.action_history[-self.stuck_threshold:]
            if len(set(recent_actions)) <= 2:  # Only 1-2 unique actions
                return True
                
        return False
    
    def get_recovery_strategy(self) -> str:
        patterns = Counter(self.action_history[-5:])
        most_common = patterns.most_common(1)[0][0] if patterns else ""
        
        if "click" in most_common:
            return "try_alternative_search"
        elif "scroll" in most_common:
            return "change_search_query"
        else:
            return "go_to_search"

# Initialize stuck detector globally
stuck_detector = StuckDetector()


async def compile_research(state: AgentState):
    system_message = """
    You are an expert academic writer compiling a rigorous, publication-quality research article from multiple subtopic sections.

    The article should follow a clear research paper structure, with the following sections:

    1. Abstract (~150 words)
       - Concise summary of the research aims, methods, key findings, and significance.

    2. Introduction (~300 words)
       - Context and background of the research problem.
       - Clear statement of objectives and research questions.
       - Importance and novelty of the study.

    3. Literature Review and Synthesis (~800 words)
       - Integrate and critically analyze findings from the subtopic sections.
       - Identify agreements, disagreements, and gaps in existing research.
       - Highlight methodologies and evidence quality.

    4. Discussion (~600 words)
       - Interpret the combined findings.
       - Discuss implications, limitations, and the broader impact.
       - Address unresolved questions or controversies.

    5. Future Research Directions (~300 words)
       - Propose specific areas needing further study.
       - Suggest potential methodological improvements.

    6. Conclusion (~200 words)
       - Summarize main contributions and insights.
       - Emphasize practical or theoretical significance.

    7. References (excluded from word count)
       - Compile all sources cited across subtopics.
       - Use consistent academic formatting (APA or similar).

    Writing style and quality expectations:
    - Maintain academic rigor with clear, precise language.
    - Ensure logical flow and seamless integration of all subtopics.
    - Provide critical analysis rather than simple summary.
    - Avoid redundancy and keep prose concise and focused.
    """

    human_prompt = """
    Research Topic: {topic}
    This is the broader research paper topic: {broader_research_paper_topic}
    This is the set of subtopic and their answers: {subtopic_answers}
    This is the list of visited urls: {visited_urls}
    
    Compile these into a comprehensive, publication-quality research paper.
    """

    broader_research_paper_topic = state["input"]
    subtopic_answers = state["subtopic_answers"]
    visited_urls = state["visited_urls"]

    human_message = human_prompt.format(
        topic=state["input"],
        broader_research_paper_topic=broader_research_paper_topic,
        subtopic_answers=subtopic_answers,
        visited_urls=visited_urls
    )

    messages = [
        SystemMessage(content=system_message),
        HumanMessage(content=human_message)
    ]

    response = llm_pro.invoke(messages)
    
    return {
        "final_answer": response.content,
        "actions_taken": [f"Compiled comprehensive research paper on {state['input']}"],
        "conversation_history": [f"User: {state['input']}", f"WebRover: {response.content}"]
    }


builder = StateGraph(AgentState)

builder.add_node("url_decide_node", url_decide_node)
builder.add_node("topic_breakdown", topic_breakdown)
builder.add_node("track_subtopic_status", track_subtopic_status)
builder.add_node("annotate_page", annotate_page)
builder.add_node("llm_call_node", llm_call_node)
builder.add_node("click", click)
builder.add_node("type", type)
builder.add_node("scroll_page", scroll_page)
builder.add_node("scroll_pdf", scroll_pdf)
builder.add_node("scroll_and_read", scroll_and_read)
builder.add_node("web_page_rag", web_page_rag)
builder.add_node("note_scroll_read", note_scroll_read)
builder.add_node("close_page", close_page)
builder.add_node("wait", wait)
builder.add_node("go_back", go_back)
builder.add_node("go_to_search", go_to_search)
builder.add_node("subtopic_answer_node", subtopic_answer_node)
builder.add_node("empty_rag_store", empty_rag_store)
builder.add_node("close_opened_link", close_opened_link)
builder.add_node("self_review", self_review)
builder.add_node("compile_research", compile_research)


builder.add_edge(START, "url_decide_node")
builder.add_edge("url_decide_node", "topic_breakdown")
builder.add_edge("topic_breakdown", "track_subtopic_status")
builder.add_conditional_edges("track_subtopic_status", research_router, ["go_to_search", "compile_research"])
builder.add_edge("annotate_page", "llm_call_node")
builder.add_conditional_edges("llm_call_node", tool_router, ["annotate_page", "click", "type", "scroll_and_read", "close_page", "wait", "go_back", "go_to_search"])
builder.add_edge("scroll_and_read", "web_page_rag")
builder.add_conditional_edges("scroll_and_read", webpage_or_pdf, ["scroll_page", "scroll_pdf"])
builder.add_edge("scroll_pdf", "note_scroll_read")
builder.add_edge("scroll_page", "note_scroll_read")
builder.add_edge("web_page_rag", "note_scroll_read")
builder.add_edge("note_scroll_read", "close_opened_link")
builder.add_edge("close_opened_link", "self_review")
builder.add_conditional_edges("self_review", after_self_router, ["annotate_page", "subtopic_answer_node"])
builder.add_edge("subtopic_answer_node", "empty_rag_store")
builder.add_edge("empty_rag_store", "track_subtopic_status")
builder.add_edge("compile_research", END)
builder.add_conditional_edges("click", after_click_router, ["annotate_page", "scroll_and_read"])
builder.add_edge("type", "annotate_page")
builder.add_edge("close_page", "annotate_page")
builder.add_edge("wait", "annotate_page")
builder.add_edge("go_back", "annotate_page")
builder.add_edge("go_to_search", "annotate_page")

deep_research_agent = builder.compile()