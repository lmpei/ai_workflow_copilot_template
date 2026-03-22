from fastapi import APIRouter

from app.schemas.scenario import ScenarioModuleDefinitionResponse, list_scenario_module_definitions

router = APIRouter()


@router.get("/scenario-modules", response_model=list[ScenarioModuleDefinitionResponse])
async def list_scenario_modules() -> list[ScenarioModuleDefinitionResponse]:
    return [
        ScenarioModuleDefinitionResponse.model_validate(module_definition)
        for module_definition in list_scenario_module_definitions()
    ]