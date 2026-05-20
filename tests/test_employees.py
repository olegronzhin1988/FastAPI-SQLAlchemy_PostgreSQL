"""
Tests for employee endpoints:
- create (POST /departments/employees/)
"""

import pytest
from httpx import AsyncClient
from typing import Dict, Any


class TestEmployeesCreate:
    """Tests for creating employees (POST /departments/employees/)"""

    @pytest.mark.asyncio
    async def test_create_employee_success(
        self,
        client: AsyncClient,
        create_test_department: Dict[str, Any],
        sample_employee_data: Dict[str, Any]
    ):
        """Successfully create an employee"""
        employee_data = {
            **sample_employee_data,
            "department_id": create_test_department["id"]
        }
        response = await client.post("/departments/employees/", json=employee_data)
        assert response.status_code == 201
        data = response.json()
        assert data["full_name"] == sample_employee_data["full_name"]
        assert data["position"] == sample_employee_data["position"]
        assert data["department_id"] == create_test_department["id"]
        assert data["hired_at"] is None
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_employee_trim_name(
        self, client: AsyncClient, create_test_department: Dict[str, Any]
    ):
        """Create employee with whitespace trimming in name"""
        response = await client.post("/departments/employees/", json={
            "full_name": "  John Smith  ",
            "position": "Developer",
            "department_id": create_test_department["id"]
        })
        assert response.status_code == 201
        data = response.json()
        assert data["full_name"] == "John Smith"  # Whitespace trimmed

    @pytest.mark.asyncio
    async def test_create_employee_with_hired_date(
        self, client: AsyncClient, create_test_department: Dict[str, Any]
    ):
        """Create employee with hire date specified"""
        from datetime import date

        response = await client.post("/departments/employees/", json={
            "full_name": "Jane Smith",
            "position": "Developer",
            "department_id": create_test_department["id"],
            "hired_at": "2025-01-15"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["hired_at"] == "2025-01-15"

    @pytest.mark.asyncio
    async def test_create_employee_invalid_department(
        self, client: AsyncClient, sample_employee_data: Dict[str, Any]
    ):
        """Create employee in non-existent department → 404"""
        employee_data = {**sample_employee_data, "department_id": 99999}
        response = await client.post("/departments/employees/", json=employee_data)
        assert response.status_code == 404
        assert "no department" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_duplicate_employee_same_department(
        self,
        client: AsyncClient,
        create_test_department: Dict[str, Any],
        sample_employee_data: Dict[str, Any]
    ):
        """Create duplicate employee in same department → 400"""
        employee_data = {
            **sample_employee_data,
            "department_id": create_test_department["id"]
        }

        # First creation
        await client.post("/departments/employees/", json=employee_data)

        # Second creation (duplicate)
        response = await client.post("/departments/employees/", json=employee_data)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_employee_same_name_different_departments(
        self,
        client: AsyncClient,
        create_test_department: Dict[str, Any]
    ):
        """
        Create employees with same name in different departments.
        This is allowed (uniqueness constraint is per department only).
        """
        # Create second department
        dept2_response = await client.post("/departments/", json={"name": "Second Department"})
        dept2_id = dept2_response.json()["id"]

        employee_data = {"full_name": "Common Name", "position": "Worker"}

        # Create in first department
        emp1_data = {**employee_data, "department_id": create_test_department["id"]}
        response1 = await client.post("/departments/employees/", json=emp1_data)
        assert response1.status_code == 201

        # Create in second department
        emp2_data = {**employee_data, "department_id": dept2_id}
        response2 = await client.post("/departments/employees/", json=emp2_data)
        assert response2.status_code == 201  # Allowed


class TestEmployeesGet:
    """Tests for retrieving employees"""

    @pytest.mark.asyncio
    async def test_employees_sorted_by_name_in_department(
        self, client: AsyncClient, create_test_department: Dict[str, Any]
    ):
        """
        Verify that employees in a department are sorted by name.
        Your GET /departments/{id} endpoint includes employee sorting.
        """
        dept_id = create_test_department["id"]

        # Create employees with different names
        await client.post("/departments/employees/", json={
            "full_name": "Zoe Anderson",
            "position": "Manager",
            "department_id": dept_id
        })
        await client.post("/departments/employees/", json={
            "full_name": "Anna Brown",
            "position": "Developer",
            "department_id": dept_id
        })

        response = await client.get(f"/departments/{dept_id}?include_employees=true")
        assert response.status_code == 200
        data = response.json()

        employees = data["employees"]
        # Should be sorted by name (Anna, Zoe)
        names = [e["full_name"] for e in employees]
        assert names == sorted(names)


class TestIntegration:
    """Integration tests (complex scenarios)"""

    @pytest.mark.asyncio
    async def test_complete_organization_workflow(self, client: AsyncClient):
        """
        Complete scenario: create company structure, move departments, delete with reassignment.
        """
        # 1. Create root company
        company_response = await client.post("/departments/", json={"name": "Acme Corp"})
        assert company_response.status_code == 201
        company_id = company_response.json()["id"]

        # 2. Create child departments
        sales_response = await client.post("/departments/", json={
            "name": "Sales",
            "parent_id": company_id
        })
        assert sales_response.status_code == 201
        sales_id = sales_response.json()["id"]

        it_response = await client.post("/departments/", json={
            "name": "IT",
            "parent_id": company_id
        })
        assert it_response.status_code == 201
        it_id = it_response.json()["id"]

        # 3. Create employees
        await client.post("/departments/employees/", json={
            "full_name": "John Sales",
            "position": "Manager",
            "department_id": sales_id
        })
        await client.post("/departments/employees/", json={
            "full_name": "Jane IT",
            "position": "Developer",
            "department_id": it_id
        })

        # 4. Verify company structure
        response = await client.get(f"/departments/{company_id}?depth=2&include_employees=true")
        assert response.status_code == 200
        data = response.json()

        assert len(data["children"]) == 2  # Sales and IT
        assert data["department"]["name"] == "Acme Corp"

        # 5. Move IT under Sales
        patch_response = await client.patch(
            f"/departments/{it_id}",
            params={"parent_id": sales_id}
        )
        assert patch_response.status_code == 202

        # 6. Verify new hierarchy
        response = await client.get(f"/departments/{sales_id}?depth=1")
        data = response.json()
        assert len(data["children"]) == 1
        assert data["children"][0]["name"] == "IT"

        # 7. Delete Sales with employee reassignment to Company
        delete_response = await client.delete(
            f"/departments/{sales_id}",
            params={"mode": "reassign", "reassign_to_department_id": company_id}
        )
        assert delete_response.status_code == 204

        # 8. Verify John Sales is now in Company
        company_response = await client.get(
            f"/departments/{company_id}?include_employees=true"
        )
        company_data = company_response.json()
        employee_names = [e["full_name"] for e in company_data["employees"]]
        assert "John Sales" in employee_names

        # 9. Cascade delete Company
        delete_response = await client.delete(
            f"/departments/{company_id}",
            params={"mode": "cascade"}
        )
        assert delete_response.status_code == 204

        # 10. Verify everything is deleted
        response = await client.get(f"/departments/{company_id}")
        assert response.status_code == 404