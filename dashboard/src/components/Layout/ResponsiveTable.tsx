import React from 'react';
import { Table, TableProps } from 'antd';
import { getDeviceType } from '../../styles/responsive';

interface ResponsiveTableProps<T> extends TableProps<T> {
  mobileCardView?: boolean;
}

/**
 * Responsive table that adapts to different screen sizes
 * On mobile, can optionally render as cards instead of table
 */
function ResponsiveTable<T extends object>({
  mobileCardView = false,
  ...props
}: ResponsiveTableProps<T>) {
  const deviceType = getDeviceType();

  // Adjust table props based on device type
  const getResponsiveProps = (): Partial<TableProps<T>> => {
    if (deviceType === 'mobile') {
      return {
        scroll: { x: 'max-content' },
        pagination: {
          ...props.pagination,
          pageSize: 10,
          simple: true,
          showSizeChanger: false
        },
        size: 'small'
      };
    }

    if (deviceType === 'tablet') {
      return {
        scroll: { x: 'max-content' },
        pagination: {
          ...props.pagination,
          pageSize: 15,
          showSizeChanger: true
        },
        size: 'middle'
      };
    }

    return {
      pagination: {
        ...props.pagination,
        pageSize: 20,
        showSizeChanger: true,
        showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} items`
      }
    };
  };

  const responsiveProps = getResponsiveProps();

  return <Table<T> {...props} {...responsiveProps} />;
}

export default ResponsiveTable;
