from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAuthorOrReadOnly(BasePermission):
    """
    - 읽기(GET, HEAD, OPTIONS): 모두 허용
    - 쓰기(POST, PUT, PATCH, DELETE): 작성자 본인만 허용
    """
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.user == request.user
