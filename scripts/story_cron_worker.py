import os
import sys
import time
import argparse
from pathlib import Path

# Add engine directory to sys.path
ENGINE_DIR = Path(__file__).resolve().parent.parent / "engine"
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from autodub.config import PROJECTS_DIR
from autodub.models.project import Project
from autodub.modules.story_collector import StoryCollector
from autodub.modules.story_cleaner import StoryCleaner
from autodub.modules.story_analyzer import StoryAnalyzer
from autodub.modules.scene_planner import ScenePlanner
from autodub.utils.logging import setup_logger

logger = setup_logger(Path.cwd() / "logs" / "cron_worker.log")

def run_story_cron_cycle(topic: str = "ghost", language: str = "en"):
    logger.info(f"=== Starting Daily Story Automation Cron Cycle (Topic: {topic}, Language: {language}) ===")
    
    # 1. Create new project directory
    proj_id = f"auto_story_{int(time.time())}"
    project_dir = PROJECTS_DIR / proj_id
    project = Project(project_dir, name=f"Auto Story - {topic.title()}", mode="MODE_STORY")
    logger.info(f"Created automated story project: {proj_id}")

    # 2. Fetch Story
    collector = StoryCollector(project)
    meta = collector.collect("gutenberg", identifier=topic, language=language)
    logger.info(f"Fetched public domain story: '{meta.get('title')}'")

    # 3. Clean Story
    cleaner = StoryCleaner()
    cleaner.clean_project_story(project)
    logger.info("Cleaned story text.")

    # 4. Analyze Story
    analyzer = StoryAnalyzer()
    analyzer.analyze_project_story(project)
    logger.info("Extracted character and world bibles.")

    # 5. Plan Scenes
    planner = ScenePlanner()
    scenes = planner.plan_chapter_scenes(project, chapter_index=1)
    logger.info(f"Planned {len(scenes)} scenes. Status set to REVIEW_REQUIRED.")

    logger.info(f"=== Cron Cycle Finished for '{proj_id}'. Project awaiting Human Review. ===")
    return project

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AutoDubStudio Daily Story Cron Worker")
    parser.add_argument("--topic", default="ghost", help="Story topic search")
    parser.add_argument("--language", default="en", help="Language code")
    args = parser.parse_args()

    run_story_cron_cycle(topic=args.topic, language=args.language)
