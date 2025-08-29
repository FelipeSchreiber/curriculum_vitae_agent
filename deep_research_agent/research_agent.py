from agents import Runner, trace, gen_trace_id, Agent, function_tool
from .search_agent import search_agent
from .planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from .writer_agent import writer_agent, ReportData
import asyncio

@function_tool
async def research_pipeline(query: str) -> str:
    """
    OpenAI agent for deep research. Yields status updates and the final report.
    """
    trace_id = gen_trace_id()
    with trace("Research trace", trace_id=trace_id):
        yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
        yield "Starting research..."
        search_plan = await plan_searches(query)
        yield "Searches planned, starting to search..."
        search_results = await perform_searches(search_plan)
        yield "Searches complete, writing report..."
        report = await write_report(query, search_results)
        yield report.markdown_report

async def plan_searches(query: str) -> WebSearchPlan:
    print("Planning searches...")
    result = await Runner.run(
        planner_agent,
        f"Query: {query}",
    )
    print(f"Will perform {len(result.final_output.searches)} searches")
    return result.final_output_as(WebSearchPlan)

async def perform_searches(search_plan: WebSearchPlan) -> list[str]:
    print("Searching...")
    num_completed = 0
    tasks = [asyncio.create_task(search(item)) for item in search_plan.searches]
    results = []
    for task in asyncio.as_completed(tasks):
        result = await task
        if result is not None:
            results.append(result)
        num_completed += 1
        print(f"Searching... {num_completed}/{len(tasks)} completed")
    print("Finished searching")
    return results

async def search(item: WebSearchItem) -> str | None:
    input = f"Search term: {item.query}\nReason for searching: {item.reason}"
    try:
        result = await Runner.run(
            search_agent,
            input,
        )
        return str(result.final_output)
    except Exception:
        return None

async def write_report(query: str, search_results: list[str]) -> ReportData:
    print("Thinking about report...")
    input = f"Original query: {query}\nSummarized search results: {search_results}"
    result = await Runner.run(
        writer_agent,
        input,
    )
    print("Finished writing report")
    return result.final_output_as(ReportData)

# Register as an Agent
research_agent = Agent(name="research_agent",
                       model="gpt-4.1-mini",
                       tools=[research_pipeline],
                       handoff_description="An agent that performs deep research on a topic and produces a report.")