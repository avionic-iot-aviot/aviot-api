from flask_restful import Resource
from flask import request
from app.api.resources.schema import OrganizationSchema
import app.models.organization
from flask_jwt_extended import jwt_required, get_jwt_identity, current_user
from app import is_admin, is_normal_user


class OrganizationEndpoint(Resource):

    @jwt_required
    @is_admin
    def post(self):

        # role: admin
        """"
        # TODO fattorizzare
        if current_user.admin is not True:
            return {
                       'error': {
                           'id': 2,
                           'description': 'permission denied',
                           'details': ""
                       }
                   }, 403
        """
        json_data = request.get_json()

        if not json_data:
            return {
                       'error': {
                           'id': 1,
                           'description': 'no input data provided or not json format',
                           'details': {}
                       }
                   }, 400  # Bad request

        # FIXME inserire organization_domain
        org_schema = OrganizationSchema()
        data, errors = org_schema.load(json_data)

        if errors:
            return {
                       'error': {
                           'id': 2,
                           'description': 'validation error',
                           'details': errors
                       }
                   }, 422

        # check if organization exists
        org_obj = app.models.organization.Organization.objects(domain=data['domain']).first()

        if org_obj is not None:
            return {
                       'error': {
                           'id': 2,
                           'description': 'organization exists',
                           'details': errors
                       }
                   }, 404

        organization = app.models.organization.Organization()
        organization.domain = data['domain']
        organization.description = data['description']
        organization.name = data['name']
        organization.save()

        return 201  # TODO controllare codice

    @jwt_required
    @is_normal_user
    def get(self):

        # role: admin, normal user
        org_obj = app.models.organization.Organization.objects(
            name=current_user.organization.name
        ).first()
        org_schema = OrganizationSchema()

        return org_schema.dump(org_obj)

