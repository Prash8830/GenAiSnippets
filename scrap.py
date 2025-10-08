import asyncio
import json
import re
from playwright.async_api import async_playwright

async def scrape_theory_content(url):
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # Navigate to the page with increased timeout and different wait strategy
            await page.goto(url, wait_until='domcontentloaded', timeout=60000)
            
            # Wait for MathJax to render
            await page.wait_for_timeout(5000)
            
            # Execute MathJax rendering if needed
            await page.evaluate("if (window.MathJax && window.MathJax.typeset) { window.MathJax.typeset(); }")
            
            # Wait a bit more for final rendering
            await page.wait_for_timeout(2000)
            
            # Extract parent and topic from URL
            # URL format: .../algebra/polynom#!/
            url_parts = [part for part in url.rstrip('/').split('/') if part]
            parent = None
            topic = None
            
            # Find algebra and polynom in the URL path
            try:
                for i, part in enumerate(url_parts):
                    # Skip protocol, domain, and common path parts
                    if 'http' in part or '.' in part or part in ['lektioner', 'gymnasiet', 'matte-niva-2']:
                        continue
                    
                    # Clean the part
                    cleaned = part.replace('#!/', '').replace('-', ' ').strip()
                    
                    if cleaned:
                        if parent is None:
                            parent = cleaned
                        elif topic is None:
                            topic = cleaned
                            break
            except:
                pass
            
            # Click on theory tab if exists
            try:
                theory_tab = await page.query_selector('text=Teori')
                if theory_tab:
                    await theory_tab.click()
                    await page.wait_for_timeout(1000)
            except:
                pass
            
            # Extract theory content from div class="body ng-scope" only
            theory_content = await page.evaluate('''
                () => {
                    const bodyDiv = document.querySelector('div.body.ng-scope');
                    if (!bodyDiv) {
                        return '';
                    }
                    return bodyDiv.innerText || bodyDiv.textContent || '';
                }
            ''')
            
            # Clean up content in Python
            if theory_content:
                # Remove excessive whitespace
                theory_content = re.sub(r'\n{3,}', '\n\n', theory_content)
                theory_content = re.sub(r'\t+', ' ', theory_content)
                theory_content = re.sub(r' {2,}', ' ', theory_content)
                theory_content = theory_content.strip()
            else:
                theory_content = 'None'
            
            # Extract all image URLs from div class="body ng-scope"
            image_urls = await page.evaluate('''
                () => {
                    const bodyDiv = document.querySelector('div.body.ng-scope');
                    if (!bodyDiv) {
                        return [];
                    }
                    const images = bodyDiv.querySelectorAll('img');
                    const urls = [];
                    images.forEach(img => {
                        let src = img.src || img.getAttribute('data-src');
                        if (src) {
                            if (src.startsWith('/')) {
                                src = window.location.origin + src;
                            } else if (!src.startsWith('http')) {
                                src = window.location.origin + '/' + src;
                            }
                            urls.push(src);
                        }
                    });
                    return [...new Set(urls)];
                }
            ''')
            
            # Create result object
            result = {
                "url": url,
                "parent": parent,
                "topic": topic,
                "content": theory_content.strip(),
                "image_urls": image_urls
            }
            
            # Save to JSON file
            with open('scraped_theory.json', 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print(f"✓ Scraped successfully!")
            print(f"✓ Parent: {parent}")
            print(f"✓ Topic: {topic}")
            print(f"✓ Content length: {len(theory_content)} characters")
            print(f"✓ Images found: {len(image_urls)}")
            print(f"✓ Saved to: scraped_theory.json")
            
            return result
            
        except Exception as e:
            print(f"Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
            
        finally:
            await browser.close()

async def main():
    url = "https://www.matteboken.se/lektioner/gymnasiet/matte-niva-2/algebra/polynom#!/"
    result = await scrape_theory_content(url)
    
    if result:
        print("\n--- Preview ---")
        print(f"Content preview: {result['content'][:300]}...")
        if result['image_urls']:
            print(f"\nImage URLs: {result['image_urls'][:3]}...")

if __name__ == "__main__":
    asyncio.run(main())