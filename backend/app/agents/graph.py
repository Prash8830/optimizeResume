from langgraph.graph import END, START, StateGraph

from app.agents.ats_checker import ats_checker, should_loop
from app.agents.content_selector import content_selector
from app.agents.jd_analyzer import jd_analyzer
from app.agents.profile_scorer import profile_scorer
from app.agents.report_gen import report_generator
from app.agents.resume_writer import resume_writer
from app.agents.state import ResumeState


def build_graph() -> StateGraph:
    graph = StateGraph(ResumeState)

    # Register all nodes
    graph.add_node("jd_analyzer", jd_analyzer)
    graph.add_node("profile_scorer", profile_scorer)
    graph.add_node("content_selector", content_selector)
    graph.add_node("resume_writer", resume_writer)
    graph.add_node("ats_checker", ats_checker)
    graph.add_node("report_generator", report_generator)

    # Linear edges
    graph.add_edge(START, "jd_analyzer")
    graph.add_edge("jd_analyzer", "profile_scorer")
    graph.add_edge("profile_scorer", "content_selector")
    graph.add_edge("content_selector", "resume_writer")
    graph.add_edge("resume_writer", "ats_checker")

    # Conditional edge: ATS checker → loop back or continue
    graph.add_conditional_edges(
        "ats_checker",
        should_loop,
        {
            "resume_writer": "resume_writer",
            "report_generator": "report_generator",
        },
    )

    graph.add_edge("report_generator", END)

    return graph.compile()
