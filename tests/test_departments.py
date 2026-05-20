"""
Tests for department endpoints:
- create (POST /departments/)
- retrieve (GET /departments/{id})
- update (PATCH /departments/{id})
- delete (DELETE /departments/{id})
"""

import pytest
from httpx import AsyncClient
from typing import Dict, Any


class TestDepartmentsCreate:
    """Tests for creating departments (POST /departments/)"""

    @pytest.mark.asyncio
    async def test_create_department_success(
        self, client: AsyncClient, sample_department_data: Dict[str, Any]
    ):
        """Successfully create a department without a parent"""
        response = await client.post("/departments/", json=sample_department_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_department_data["name"]
        assert data["parent_id"] is None
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_department_trim_name(
        self, client: AsyncClient
    ):
        """Create department with whitespace trimming in name"""
        response = await client.post("/departments/", json={"name": "  IT Department  "})
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "IT Department"  # Whitespace trimmed

    @pytest.mark.asyncio
    async def test_create_department_with_parent(
        self, client: AsyncClient, create_test_department: Dict[str, Any]
    ):
        """Create a child department"""
        child_data = {
            "name": "Child Department",
            "parent_id": create_test_department["id"]
        }
        response = await client.post("/departments/", json=child_data)
        assert response.status_code == 201
        data = response.json()
        assert data["parent_id"] == create_test_department["id"]

    @pytest.mark.asyncio
    async def test_create_department_with_invalid_parent(
        self, client: AsyncClient
    ):
        """Create department with non-existent parent → 404"""
        response = await client.post("/departments/", json={
            "name": "Invalid Dept",
            "parent_id": 99999
        })
        assert response.status_code == 404
        assert "no department" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_duplicate_department_same_parent(
        self, client: AsyncClient, create_test_department: Dict[str, Any]
    ):
        """Create duplicate department (same name and parent_id) → 400"""
# First creation
        await client.post("/departments/", json={
            "name": "Duplicate Dept",
            "parent_id": create_test_department["id"]
        })

# Second creation (duplicate)
        response = await client.post("/departments/", json={
            "name": "Duplicate Dept",
            "parent_id": create_test_department["id"]
        })
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_duplicate_department_different_parent(
        self, client: AsyncClient
    ):
        """Create departments with same name but different parents → allowed"""
# Create first parent and child department
        parent1 = await client.post("/departments/", json={"name": "Parent 1"})
        parent1_id = parent1.json()["id"]

        response1 = await client.post("/departments/", json={
            "name": "Same Name",
            "parent_id": parent1_id
        })
        assert response1.status_code == 201

# Create second parent and child department with the same name
        parent2 = await client.post("/departments/", json={"name": "Parent 2"})
        parent2_id = parent2.json()["id"]

        response2 = await client.post("/departments/", json={
            "name": "Same Name",
            "parent_id": parent2_id
        })
        assert response2.status_code == 201  # Allowed


class TestDepartmentsGet:
    """Tests for retrieving departments (GET /departments/{id})"""

    @pytest.mark.asyncio
    async def test_get_department_success(
        self, client: AsyncClient, create_test_department: Dict[str, Any]
    ):
        """Successfully retrieve a department by ID"""
        dept_id = create_test_department["id"]
        response = await client.get(f"/departments/{dept_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["department"]["id"] == dept_id
        assert data["department"]["name"] == create_test_department["name"]
        assert "employees" in data
        assert "children" in data

    @pytest.mark.asyncio
    async def test_get_department_not_found(self, client: AsyncClient):
        """Retrieve non-existent department → 404"""
        response = await client.get("/departments/99999")
        assert response.status_code == 404
        assert "no department" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_department_with_employees(
        self, client: AsyncClient, create_test_employee: Dict[str, Any]
    ):
        """Retrieve department with employees (include_employees=true)"""
        dept_id = create_test_employee["department_id"]
        response = await client.get(
            f"/departments/{dept_id}?include_employees=true"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["employees"]) >= 1
        assert data["employees"][0]["full_name"] == create_test_employee["full_name"]

    @pytest.mark.asyncio
    async def test_get_department_without_employees(
        self, client: AsyncClient, create_test_department: Dict[str, Any]
    ):
        """Retrieve department without employees (include_employees=false)"""
        dept_id = create_test_department["id"]
        response = await client.get(
            f"/departments/{dept_id}?include_employees=false"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["employees"] == []

    @pytest.mark.asyncio
    async def test_get_department_with_children_depth_1(
        self, client: AsyncClient, create_test_department_with_child: Dict[str, Any]
    ):
        """Retrieve department with children at depth 1"""
        parent_id = create_test_department_with_child["parent"]["id"]
        response = await client.get(f"/departments/{parent_id}?depth=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data["children"]) == 1
        assert data["children"][0]["name"] == create_test_department_with_child["child"]["name"]

    @pytest.mark.asyncio
    async def test_get_department_with_children_depth_2(
        self, client: AsyncClient, create_test_department: Dict[str, Any]
    ):
        """Retrieve department with children at depth 2"""
        parent_id = create_test_department["id"]

# Create a child
        child_response = await client.post("/departments/", json={
            "name": "Child Dept",
            "parent_id": parent_id
        })
        child_id = child_response.json()["id"]

# Create a grandchild
        await client.post("/departments/", json={
            "name": "Grandchild Dept",
            "parent_id": child_id
        })

        response = await client.get(f"/departments/{parent_id}?depth=2")
        assert response.status_code == 200
        data = response.json()

# Should have one child at depth 1
        assert len(data["children"]) == 1
        assert data["children"][0]["name"] == "Child Dept"

# Child should have one grandchild at depth 2
        assert len(data["children"][0]["children"]) == 1
        assert data["children"][0]["children"][0]["name"] == "Grandchild Dept"


class TestDepartmentsUpdate:
    """Tests for updating departments (PATCH /departments/{id})"""

    @pytest.mark.asyncio
    async def test_update_department_parent_by_id(
        self, client: AsyncClient, create_test_department: Dict[str, Any]
    ):
        """Update department parent by id"""
# Create a new parent
        new_parent_response = await client.post("/departments/", json={"name": "New Parent"})
        new_parent_id = new_parent_response.json()["id"]

        dept_id = create_test_department["id"]
        response = await client.patch(
            f"/departments/{dept_id}",
            params={"parent_id": new_parent_id}
        )
        assert response.status_code == 202
        data = response.json()
        assert data["parent_id"] == new_parent_id

    @pytest.mark.asyncio
    async def test_update_department_parent_by_name(
        self, client: AsyncClient, create_test_department: Dict[str, Any]
    ):
        """Update department parent by providing parent's name"""
        
# Create a new department that will become the parent
        new_parent_response = await client.post("/departments/", json={"name": "Parent By Name"})
        new_parent_name = new_parent_response.json()["name"]
        new_parent_id = new_parent_response.json()["id"]
        
        dept_id = create_test_department["id"]

        response = await client.patch(
            f"/departments/{dept_id}",
            params={"name": new_parent_name}
        )
        assert response.status_code == 202
        data = response.json()
        assert data["parent_id"] == new_parent_id


    @pytest.mark.asyncio
    async def test_update_department_remove_parent(
        self, client: AsyncClient, create_test_department_with_child: Dict[str, Any]
    ):
        """Remove parent relationship (parent_id = None)"""
        child_id = create_test_department_with_child["child"]["id"]
        
# To remove parent you shouldn`t add any new parent data 
        response = await client.patch(
            f"/departments/{child_id}",
            params={}
        )
        assert response.status_code == 202
        data = response.json()
        assert data["parent_id"] is None

    @pytest.mark.asyncio
    async def test_update_department_self_parent_forbidden(
        self, client: AsyncClient, create_test_department: Dict[str, Any]
    ):
        """Prevent setting department as its own parent → 400"""
        dept_id = create_test_department["id"]
        response = await client.patch(
            f"/departments/{dept_id}",
            params={"parent_id": dept_id}
        )
        assert response.status_code == 400
        assert "cannot be its own parent" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_update_department_to_descendant_forbidden(
        self, client: AsyncClient, create_test_department: Dict[str, Any]
    ):
        """Prevent moving department under its own descendant → 400"""
        parent_id = create_test_department["id"]

# Create a child
        child_response = await client.post("/departments/", json={
            "name": "Child Dept",
            "parent_id": parent_id
        })
        child_id = child_response.json()["id"]

# Attempt to move parent under child (would create a cycle)
        response = await client.patch(
            f"/departments/{parent_id}",
            params={"parent_id": child_id}
        )
        assert response.status_code == 400
        assert "cannot be moved under its own descendant" in response.json()["detail"].lower()


class TestDepartmentsDelete:
    """Tests for deleting departments (DELETE /departments/{id})"""

    @pytest.mark.asyncio
    async def test_delete_department_cascade(
        self, client: AsyncClient, create_test_department: Dict[str, Any]
    ):
        """Cascade delete of department (mode=cascade)"""
        dept_id = create_test_department["id"]

# Create an employee
        await client.post("/departments/employees/", json={
            "full_name": "Test Employee",
            "position": "Tester",
            "department_id": dept_id
        })

# Delete department in cascade mode
        response = await client.delete(
            f"/departments/{dept_id}",
            params={"mode": "cascade"}
        )
        assert response.status_code == 204

# Verify department was deleted
        get_response = await client.get(f"/departments/{dept_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_department_reassign_success(
        self, client: AsyncClient, create_test_department: Dict[str, Any]
    ):
        """Delete department with employee reassignment (mode=reassign)"""
        dept_id = create_test_department["id"]

# Create target department
        target_response = await client.post("/departments/", json={"name": "Target Dept"})
        target_id = target_response.json()["id"]

# Create an employee
        await client.post("/departments/employees/", json={
            "full_name": "Test Employee",
            "position": "Tester",
            "department_id": dept_id
        })

# Delete department with reassignment
        response = await client.delete(
            f"/departments/{dept_id}",
            params={"mode": "reassign", "reassign_to_department_id": target_id}
        )
        assert response.status_code == 204

# Verify department was deleted
        get_response = await client.get(f"/departments/{dept_id}")
        assert get_response.status_code == 404

# Verify employee is now in target department
        target_get_response = await client.get(
            f"/departments/{target_id}?include_employees=true"
        )
        assert target_get_response.status_code == 200
        employees = target_get_response.json()["employees"]
        employee_names = [e["full_name"] for e in employees]
        assert "Test Employee" in employee_names

    @pytest.mark.asyncio
    async def test_delete_department_reassign_without_target(
        self, client: AsyncClient, create_test_department: Dict[str, Any]
    ):
        """Error: reassign mode without target department → 400"""
        dept_id = create_test_department["id"]
        response = await client.delete(
            f"/departments/{dept_id}",
            params={"mode": "reassign"}
        )
        assert response.status_code == 400
        assert "reassign_to_department_id is required" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_delete_department_reassign_same_id(
        self, client: AsyncClient, create_test_department: Dict[str, Any]
    ):
        """Error: reassign to the same department → 400"""
        dept_id = create_test_department["id"]
        response = await client.delete(
            f"/departments/{dept_id}",
            params={"mode": "reassign", "reassign_to_department_id": dept_id}
        )
        assert response.status_code == 400
        assert "cannot reassign employees to the same department" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_delete_department_reassign_invalid_target(
        self, client: AsyncClient, create_test_department: Dict[str, Any]
    ):
        """Error: reassign to non-existent department → 404"""
        dept_id = create_test_department["id"]
        response = await client.delete(
            f"/departments/{dept_id}",
            params={"mode": "reassign", "reassign_to_department_id": 99999}
        )
        assert response.status_code == 404
        assert "no department" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_delete_department_not_found(self, client: AsyncClient):
        """Delete non-existent department → 404"""
        response = await client.delete("/departments/99999", params={"mode": "cascade"})
        assert response.status_code == 404