import asyncio
import json
import os
import time
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import SecretStr

from browser_use import Agent, BrowserConfig
from browser_use.browser.browser import Browser
from browser_use.browser.context import BrowserContextConfig

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    raise ValueError('GEMINI_API_KEY is not set')

llm = ChatGoogleGenerativeAI(model='gemini-2.0-flash-exp', api_key=SecretStr(api_key))

browser = Browser(
    config=BrowserConfig(
        new_context_config=BrowserContextConfig(
            viewport_expansion=0,
        )
    )
)

BENCHMARK_TASKS = [
    "Search for 'OpenAI' on Google and summarize the results.",
    "Go to Wikipedia and find the founder of Microsoft.",
    "Visit IMDb and list top 3 rated movies.",
    "Search for the current weather in New York.",
]

class TaskTimer:
    def __init__(self):
        self.start_time = time.time()
        self.segments = {}
        self.current_segment = None
        self.segment_start = None
    
    def start_segment(self, name: str):
        if self.current_segment:
            self.end_segment()
        self.current_segment = name
        self.segment_start = time.time()
    
    def end_segment(self):
        if self.current_segment and self.segment_start:
            duration = time.time() - self.segment_start
            self.segments[self.current_segment] = duration
            self.current_segment = None
            self.segment_start = None
    
    def total_time(self):
        return time.time() - self.start_time
    
    def get_metrics(self):
        self.end_segment()  # Ensure last segment is closed
        return {
            "total_time": self.total_time(),
            "segments": self.segments
        }

async def run_agent_task(task: str, max_steps: int = 25) -> Dict[str, Any]:
    timer = TaskTimer()
    timer.start_segment("initialization")
    
    agent = Agent(
        task=task,
        llm=llm,
        max_actions_per_step=4,
        browser=browser,
    )
    
    result_content = None
    error = None
    
    timer.start_segment("execution")
    try:
        result = await agent.run(max_steps=max_steps)
        result_content = str(result)[:1000]  # Truncate if too large
        timer.start_segment("result_processing")
    except Exception as e:
        error = str(e)
    finally:
        metrics = timer.get_metrics()
    
    return {
        "task": task,
        "success": error is None,
        "result": result_content,
        "error": error,
        "time_metrics": metrics,
        "max_steps": max_steps
    }

async def run_benchmark(tasks: List[str] = BENCHMARK_TASKS) -> List[Dict[str, Any]]:
    results = []
    
    for i, task in enumerate(tasks):
        print(f"\n🧠 Task {i+1}/{len(tasks)}: {task}")
        result = await run_agent_task(task)
        results.append(result)
        
        if result["success"]:
            print(f"✅ Completed in {result['time_metrics']['total_time']:.2f}s")
            print(f"   Breakdown: {json.dumps(result['time_metrics']['segments'], indent=2)}")
        else:
            print(f"❌ Failed after {result['time_metrics']['total_time']:.2f}s: {result['error']}")
    
    return results

def save_results(results: List[Dict[str, Any]], filename: str = "benchmark_results.json"):
    output = {
        "metadata": {
            "model": "gemini-2.0-flash-exp",
            "total_tasks": len(results),
            "successful_tasks": sum(1 for r in results if r["success"]),
            "success_rate": sum(1 for r in results if r["success"]) / len(results),
            "average_time": sum(r['time_metrics']['total_time'] for r in results) / len(results),
        },
        "tasks": results
    }
    
    with open(filename, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"\n📊 Results saved to {filename}")

def print_summary(results: List[Dict[str, Any]]):
    print("\n📊 Benchmark Summary:")
    success_count = sum(1 for r in results if r["success"])
    avg_time = sum(r['time_metrics']['total_time'] for r in results) / len(results)
    avg_success_time = sum(r['time_metrics']['total_time'] for r in results if r["success"]) / max(1, success_count)
    
    print(f"Tasks: {len(results)} | Successful: {success_count} | Success Rate: {success_count/len(results):.1%}")
    print(f"Average Time (all tasks): {avg_time:.2f}s")
    print(f"Average Time (successful only): {avg_success_time:.2f}s")
    
    for r in results:
        status = "✅" if r["success"] else "❌"
        print(f"\n{status} {r['task'][:60]}...")
        print(f"Time: {r['time_metrics']['total_time']:.2f}s | Steps: {r['max_steps']}")
        if r["success"]:
            print(f"Result: {r['result'][:100]}...")
        else:
            print(f"Error: {r['error']}")
        print("Time Breakdown:")
        for segment, duration in r['time_metrics']['segments'].items():
            print(f"  {segment}: {duration:.2f}s")

async def main():
    print("🚀 Starting benchmark with detailed timing...")
    results = await run_benchmark()
    print_summary(results)
    save_results(results)

if __name__ == '__main__':
    asyncio.run(main())